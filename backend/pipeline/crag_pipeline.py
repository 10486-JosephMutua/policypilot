"""
PolicyPilot – CRAG + Self-RAG Pipeline (LangGraph orchestration)

Implements the full Corrective RAG loop from arxiv 2401.15884 extended with:
  • Self-RAG reflection tokens (IsRel / IsSup / IsUse)
  • Tri-layer confidence scoring
  • Sentence-level citation anchoring
  • Challenge / self-correction loop (re-queries with expanded context)
  • Temporal flag: warns when source may be outdated

State machine (LangGraph):
  retrieve → rerank → assess_retrieval → [correct | ambiguous | incorrect]
      ↓                                         ↓          ↓         ↓
  generate ←──────────────────────────── generate   web_augment  reformulate
      ↓
  verify_claims
      ↓
  build_graph

The Challenge loop re-enters at `retrieve` with a reformulated query.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, TypedDict, Annotated
import operator

import anthropic

from logger_config import pipeline_log as log, log_step
import config
from pipeline.retriever        import retrieve_passages
from pipeline.reranker         import rerank_passages
from pipeline.confidence_scorer import (
    score_document_level,
    verify_claims,
    aggregate_confidence,
)
from pipeline.citation_graph   import build_citation_graph

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    log.warning("langgraph not installed – falling back to sequential pipeline")


# ── LLM client ────────────────────────────────────────────────────────────────
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import config

def _llm(system: str, user: str, max_tokens: int = config.LLM_MAX_TOKENS) -> str:
    # Initialize the Groq client
    # Ensure GROQ_API_KEY is added to your .env file
    llm = ChatGroq(
        model=config.LLM_MODEL, # e.g., "llama-3.3-70b-versatile"
        temperature=0, 
        max_tokens=max_tokens,
        api_key=config.GROQ_API_KEY
    )
    
    log.debug(f"LLM call", extra={"system_len": len(system), "user_len": len(user)})
    
    # Construct messages
    messages = [
        SystemMessage(content=system),
        HumanMessage(content=user)
    ]
    
    # Invoke the model
    response = llm.invoke(messages)
    
    return response.content.strip()
    
# ── Pipeline state ─────────────────────────────────────────────────────────────
class PipelineState(TypedDict):
    query:              str
    original_query:     str
    passages:           List[Dict[str, Any]]
    reranked:           List[Dict[str, Any]]
    doc_confidence:     float
    doc_label:          str
    answer:             str
    verified_claims:    List[Dict[str, Any]]
    confidence:         Dict[str, Any]
    citation_graph:     Dict[str, Any]
    loop_count:         int
    is_challenge:       bool
    challenge_context:  str
    temporal_flags:     List[str]
    retrieval_action:   str   # Correct | Ambiguous | Incorrect


# ── Pipeline nodes ─────────────────────────────────────────────────────────────
def node_retrieve(state: PipelineState) -> PipelineState:
    log.info(f"[node_retrieve] query='{state['query'][:80]}'")
    passages = retrieve_passages(state["query"], top_k=config.TOP_K_RETRIEVE)
    return {**state, "passages": passages}


def node_rerank(state: PipelineState) -> PipelineState:
    log.info(f"[node_rerank] {len(state['passages'])} passages")
    reranked = rerank_passages(state["query"], state["passages"])
    return {**state, "reranked": reranked}


def node_assess(state: PipelineState) -> PipelineState:
    doc_conf, doc_label = score_document_level(state["query"], state["reranked"])
    log.info(f"[node_assess] doc_conf={doc_conf} label={doc_label}")
    return {**state, "doc_confidence": doc_conf, "doc_label": doc_label, "retrieval_action": doc_label}


def _routing(state: PipelineState) -> str:
    """LangGraph conditional routing function."""
    label = state.get("doc_label", "Incorrect")
    log.info(f"[routing] → {label}")
    if label == "Correct":
        return "generate_from_retrieved"
    elif label == "Ambiguous":
        return "generate_with_caveat"
    else:
        return "reformulate_query"


def node_generate_correct(state: PipelineState) -> PipelineState:
    return _generate(state, mode="confident")


def node_generate_ambiguous(state: PipelineState) -> PipelineState:
    return _generate(state, mode="cautious")


def node_reformulate(state: PipelineState) -> PipelineState:
    """Self-RAG: reformulate query when retrieval quality is poor."""
    loop = state.get("loop_count", 0)
    if loop >= config.MAX_SELF_CORRECTION_LOOPS:
        log.warning("[node_reformulate] Max loops reached – generating with disclaimer")
        return _generate(state, mode="low_confidence")

    system = (
        "You are a legal query reformulation expert. "
        "Expand the query with synonyms and related legal terms to improve document retrieval. "
        "Return ONLY the reformulated query, nothing else."
    )
    new_query = _llm(system, f"Original query: {state['query']}")
    log.info(f"[node_reformulate] Reformulated: '{new_query[:80]}'")
    return {**state, "query": new_query, "loop_count": loop + 1}


def _generate(state: PipelineState, mode: str) -> PipelineState:
    """Core generation step with passage-grounded prompting."""
    log.info(f"[_generate] mode={mode}")
    reranked = state["reranked"]

    if not reranked:
        return {**state, "answer": "Insufficient source material found to answer this query reliably."}

    passages_text = "\n\n".join(
        f"[SOURCE {i+1}] {p['metadata'].get('source_name','Unknown')} "
        f"(relevance: {p.get('rerank_score', p.get('similarity',0)):.2f}):\n{p['text']}"
        for i, p in enumerate(reranked[:5])
    )

    mode_instructions = {
        "confident":      "Answer directly and precisely. Cite source numbers inline.",
        "cautious":       "Answer with appropriate caveats where sources are incomplete. Cite sources.",
        "low_confidence": "You have limited source material. Clearly state uncertainty. Do NOT fabricate.",
    }

    challenge_ctx = ""
    if state.get("is_challenge") and state.get("challenge_context"):
        challenge_ctx = f"\n\nCHALLENGE CONTEXT: {state['challenge_context']}"

    system = (
        "You are PolicyPilot, a hallucination-proof legal and compliance AI. "
        "RULES:\n"
        "1. Only use information from the provided sources.\n"
        "2. If a source does not support a claim, do NOT make the claim.\n"
        "3. Do not use parametric (training) knowledge for legal facts.\n"
        "4. Write clear, professional prose.\n"
        f"5. {mode_instructions[mode]}"
    )

    user = (
        f"QUERY: {state['original_query']}\n\n"
        f"RETRIEVED SOURCES:\n{passages_text}"
        f"{challenge_ctx}\n\n"
        "Provide a thorough, grounded answer."
    )

    answer = _llm(system, user)

    # Temporal flag detection
    temporal_flags: List[str] = []
    year_mentions = re.findall(r'\b(19|20)\d{2}\b', answer)
    for yr in set(year_mentions):
        if int(yr) < 2022:
            temporal_flags.append(
                f"Answer references {yr} – verify this information is still current law/policy."
            )

    return {**state, "answer": answer, "temporal_flags": temporal_flags}


def node_verify(state: PipelineState) -> PipelineState:
    log.info("[node_verify] Decomposing and verifying claims")
    verified = verify_claims(state["answer"], state["reranked"])
    confidence = aggregate_confidence(verified)
    return {**state, "verified_claims": verified, "confidence": confidence}


def node_build_graph(state: PipelineState) -> PipelineState:
    log.info("[node_build_graph] Building citation graph")
    g = build_citation_graph(
        state["original_query"],
        state["answer"],
        state["verified_claims"],
        state["reranked"],
    )
    return {**state, "citation_graph": g}


# ── LangGraph builder ─────────────────────────────────────────────────────────
def _build_graph():
    if not LANGGRAPH_AVAILABLE:
        return None

    g = StateGraph(PipelineState)
    g.add_node("retrieve",                 node_retrieve)
    g.add_node("rerank",                   node_rerank)
    g.add_node("assess",                   node_assess)
    g.add_node("generate_from_retrieved",  node_generate_correct)
    g.add_node("generate_with_caveat",     node_generate_ambiguous)
    g.add_node("reformulate_query",        node_reformulate)
    g.add_node("verify",                   node_verify)
    g.add_node("build_graph",              node_build_graph)

    g.set_entry_point("retrieve")
    g.add_edge("retrieve", "rerank")
    g.add_edge("rerank",   "assess")

    g.add_conditional_edges(
        "assess",
        _routing,
        {
            "generate_from_retrieved": "generate_from_retrieved",
            "generate_with_caveat":    "generate_with_caveat",
            "reformulate_query":       "reformulate_query",
        },
    )

    # After reformulation → re-retrieve
    g.add_edge("reformulate_query",       "retrieve")
    g.add_edge("generate_from_retrieved", "verify")
    g.add_edge("generate_with_caveat",    "verify")
    g.add_edge("verify",                  "build_graph")
    g.add_edge("build_graph",             END)

    return g.compile()


_GRAPH = None


def _get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_graph()
    return _GRAPH


# ── Sequential fallback ───────────────────────────────────────────────────────
def _run_sequential(state: PipelineState) -> PipelineState:
    """Fallback pipeline when LangGraph is not available."""
    state = node_retrieve(state)
    state = node_rerank(state)
    state = node_assess(state)

    for _ in range(config.MAX_SELF_CORRECTION_LOOPS + 1):
        label = state["doc_label"]
        if label == "Correct":
            state = node_generate_correct(state)
            break
        elif label == "Ambiguous":
            state = node_generate_ambiguous(state)
            break
        else:
            state = node_reformulate(state)
            state = node_retrieve(state)
            state = node_rerank(state)
            state = node_assess(state)
    else:
        state = _generate(state, mode="low_confidence")

    state = node_verify(state)
    state = node_build_graph(state)
    return state


# ── Public API ─────────────────────────────────────────────────────────────────
@log_step(log, "run_pipeline")
def run_pipeline(
    query: str,
    is_challenge: bool = False,
    challenge_context: str = "",
) -> Dict[str, Any]:
    """
    Run the full CRAG + Self-RAG pipeline for a query.
    Returns a structured result dict.
    """
    log.info(
        f"Pipeline start",
        extra={"query": query[:80], "is_challenge": is_challenge},
    )

    initial_state: PipelineState = {
        "query":             query,
        "original_query":    query,
        "passages":          [],
        "reranked":          [],
        "doc_confidence":    0.0,
        "doc_label":         "Incorrect",
        "answer":            "",
        "verified_claims":   [],
        "confidence":        {},
        "citation_graph":    {},
        "loop_count":        0,
        "is_challenge":      is_challenge,
        "challenge_context": challenge_context,
        "temporal_flags":    [],
        "retrieval_action":  "Incorrect",
    }

    graph = _get_graph()
    if graph:
        log.info("Running via LangGraph")
        final = graph.invoke(initial_state)
    else:
        log.info("Running sequential fallback")
        final = _run_sequential(initial_state)

    result = {
        "query":           final["original_query"],
        "answer":          final["answer"],
        "confidence":      final["confidence"],
        "retrieval_action": final["retrieval_action"],
        "verified_claims": final["verified_claims"],
        "citation_graph":  final["citation_graph"],
        "sources":         [
            {
                "source_name":   p["metadata"].get("source_name", "Unknown"),
                "doc_id":        p["metadata"].get("doc_id", ""),
                "chunk_index":   p["metadata"].get("chunk_index", 0),
                "rerank_score":  p.get("rerank_score", 0),
                "text_snippet":  p["text"][:200],
                "sentences":     p.get("sentences", []),
            }
            for p in final["reranked"]
        ],
        "temporal_flags":  final.get("temporal_flags", []),
        "loop_count":      final.get("loop_count", 0),
    }

    log.info(
        f"Pipeline complete",
        extra={
            "answer_len":    len(result["answer"]),
            "confidence":    result["confidence"].get("score"),
            "claims":        len(result["verified_claims"]),
        },
    )
    return result
