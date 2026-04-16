"""
PolicyPilot – Cross-Encoder Re-ranker
Re-scores retrieved passages using a cross-encoder (ms-marco-MiniLM) which
scores (query, passage) jointly — significantly more accurate than bi-encoder
cosine similarity for precision-sensitive legal tasks.

Based on: "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks"
and the ms-marco fine-tuned cross-encoder variants.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional

from sentence_transformers import CrossEncoder

from logger_config import reranker_log as log, log_step
import config


class _Reranker:
    _instance: Optional["_Reranker"] = None

    def __init__(self):
        log.info(f"Loading cross-encoder: {config.RERANK_MODEL}")
        self._model = CrossEncoder(config.RERANK_MODEL, max_length=512)

    @classmethod
    def get(cls) -> "_Reranker":
        if cls._instance is None:
            cls._instance = _Reranker()
        return cls._instance

    def score(self, query: str, passages: List[str]) -> List[float]:
        pairs = [(query, p) for p in passages]
        scores = self._model.predict(pairs, convert_to_numpy=True).tolist()
        return scores


@log_step(log, "rerank_passages")
def rerank_passages(
    query: str,
    passages: List[Dict[str, Any]],
    top_k: int = config.TOP_K_RERANK,
) -> List[Dict[str, Any]]:
    """
    Re-rank passages using a cross-encoder.  Adds `rerank_score` to each passage
    and returns the top-k passages sorted by that score (descending).
    """
    if not passages:
        return []

    log.info(
        f"Re-ranking {len(passages)} passages → top {top_k}",
        extra={"query": query[:80]},
    )

    reranker = _Reranker.get()
    texts = [p["text"] for p in passages]
    scores = reranker.score(query, texts)

    # Attach score
    for passage, score in zip(passages, scores):
        # Normalise: cross-encoder raw scores are logits; sigmoid → [0,1]
        import math
        normalised = 1.0 / (1.0 + math.exp(-score))
        passage["rerank_score"] = round(normalised, 4)

    ranked = sorted(passages, key=lambda p: p["rerank_score"], reverse=True)
    top = ranked[:top_k]

    log.info(
        f"Top-{top_k} rerank scores: "
        + str([p["rerank_score"] for p in top])
    )
    return top
