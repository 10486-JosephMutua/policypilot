"""
PolicyPilot – Tri-Layer Confidence Scorer

Implements the CRAG confidence framework extended to three layers:
  1. Document-level   – how relevant is the retrieved corpus?
  2. Passage-level    – how relevant is the specific passage?
  3. Claim-level      – is each generated claim grounded in retrieved text?

CRAG thresholds:
  score >= CONFIDENCE_HIGH  → Correct   (use as-is)
  score <  CONFIDENCE_LOW   → Incorrect (trigger fallback / web search)
  otherwise                 → Ambiguous (hybrid strategy)

References:
  Shi et al. 2024 – "Large Legal Fictions" (hallucination taxonomy)
  CRAG (arxiv 2401.15884) – confidence-triggered retrieval actions
  Self-RAG (arxiv 2310.11511) – reflection tokens (IsRel, IsSup, IsUse)
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer, util

from logger_config import confidence_log as log, log_step
import config

_SIM_MODEL: SentenceTransformer | None = None


def _sim_model() -> SentenceTransformer:
    global _SIM_MODEL
    if _SIM_MODEL is None:
        log.info("Loading similarity model for confidence scoring")
        _SIM_MODEL = SentenceTransformer(config.EMBEDDING_MODEL)
    return _SIM_MODEL


def _cosine(a: str, b: str) -> float:
    """Fast cosine similarity between two strings."""
    model = _sim_model()
    embs = model.encode([a, b], convert_to_tensor=True)
    return float(util.cos_sim(embs[0], embs[1]))


# ── Layer 1: Document-level confidence ────────────────────────────────────────
@log_step(log, "score_document_level")
def score_document_level(
    query: str,
    passages: List[Dict[str, Any]],
) -> Tuple[float, str]:
    """
    Average top-k rerank scores → aggregate document relevance confidence.
    Returns (score, label) where label ∈ {Correct, Ambiguous, Incorrect}.
    """
    if not passages:
        return 0.0, "Incorrect"

    scores = [p.get("rerank_score", p.get("similarity", 0.0)) for p in passages]
    avg = float(np.mean(scores))
    label = _label(avg)
    log.info(
        f"Document-level confidence",
        extra={"score": avg, "label": label, "n_passages": len(passages)},
    )
    return round(avg, 4), label


# ── Layer 2: Passage-level sentence attribution ───────────────────────────────
@log_step(log, "score_passage_level")
def score_passage_level(
    claim: str,
    passage: Dict[str, Any],
) -> Dict[str, Any]:
    """
    For a single claim string, find the sentence(s) in the passage that best
    support it.  Returns the sentence, its index, and a grounding score.
    """
    sentences = passage.get("sentences", [])
    if not sentences:
        sentences = [passage["text"]]

    best_score = -1.0
    best_sent  = ""
    best_idx   = 0

    for i, sent in enumerate(sentences):
        s = _cosine(claim, sent)
        if s > best_score:
            best_score = s
            best_sent  = sent
            best_idx   = i

    return {
        "sentence": best_sent,
        "sentence_index": best_idx,
        "grounding_score": round(best_score, 4),
        "source_name": passage["metadata"].get("source_name", "Unknown"),
        "doc_id": passage["metadata"].get("doc_id", ""),
        "chunk_index": passage["metadata"].get("chunk_index", 0),
    }


# ── Layer 3: Claim-level verification ─────────────────────────────────────────
@log_step(log, "verify_claims")
def verify_claims(
    answer: str,
    passages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Decompose the answer into atomic claims (sentences), verify each against
    all passages, and return a per-claim verification record.

    Implements the FactChecker pattern from HalluDetect (2025):
      Decompose → Verify each claim → Synthesise confidence.
    """
    claims = _split_claims(answer)
    log.info(f"Verifying {len(claims)} claims")

    verified: List[Dict[str, Any]] = []
    for claim_text in claims:
        best_support: Dict[str, Any] = {}
        best_score = -1.0

        for passage in passages:
            support = score_passage_level(claim_text, passage)
            if support["grounding_score"] > best_score:
                best_score = support["grounding_score"]
                best_support = support

        claim_label = _label(best_score)
        log.debug(
            f"Claim verified",
            extra={
                "claim": claim_text[:60],
                "score": best_score,
                "label": claim_label,
            },
        )
        verified.append(
            {
                "claim": claim_text,
                "confidence": round(best_score, 4),
                "label": claim_label,
                "citation": best_support,
            }
        )

    return verified


# ── Overall answer confidence ─────────────────────────────────────────────────
def aggregate_confidence(verified_claims: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate per-claim confidences into a single answer-level score."""
    if not verified_claims:
        return {"score": 0.0, "label": "Incorrect", "details": {}}

    scores = [c["confidence"] for c in verified_claims]
    mean_score  = float(np.mean(scores))
    min_score   = float(np.min(scores))
    # Penalise if any claim is weakly supported
    overall = mean_score * 0.7 + min_score * 0.3
    label = _label(overall)

    correct_n   = sum(1 for c in verified_claims if c["label"] == "Correct")
    ambiguous_n = sum(1 for c in verified_claims if c["label"] == "Ambiguous")
    incorrect_n = sum(1 for c in verified_claims if c["label"] == "Incorrect")

    return {
        "score": round(overall, 4),
        "label": label,
        "details": {
            "mean": round(mean_score, 4),
            "min":  round(min_score,  4),
            "correct":   correct_n,
            "ambiguous": ambiguous_n,
            "incorrect": incorrect_n,
            "total":     len(verified_claims),
        },
    }


# ── Helpers ───────────────────────────────────────────────────────────────────
def _label(score: float) -> str:
    if score >= config.CONFIDENCE_HIGH:
        return "Correct"
    if score < config.CONFIDENCE_LOW:
        return "Incorrect"
    return "Ambiguous"


def _split_claims(text: str) -> List[str]:
    """Split answer text into atomic claim sentences."""
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in raw if len(s.strip()) > 20]
