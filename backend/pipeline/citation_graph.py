"""
PolicyPilot – Citation Graph Builder

Builds a directed provenance graph: Query → Answer → Claims → Source Sentences.
Serialises to a format consumable by the React frontend (nodes + edges).

The graph makes hallucination visible: any claim with no edge to a source node
is immediately suspect.
"""

from __future__ import annotations

from typing import List, Dict, Any
from logger_config import graph_log as log, log_step


@log_step(log, "build_citation_graph")
def build_citation_graph(
    query: str,
    answer: str,
    verified_claims: List[Dict[str, Any]],
    passages: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Return a {nodes, edges} graph suitable for a D3 / React Flow renderer.

    Node types:
      query   – the original user query
      answer  – the generated answer block
      claim   – an atomic factual claim extracted from the answer
      source  – a source document passage

    Edge types:
      generates  – query → answer
      contains   – answer → claim
      supported_by – claim → source (with grounding_score)
    """
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    # ── Query node ────────────────────────────────────────────────────────────
    query_id = "node_query"
    nodes.append({"id": query_id, "type": "query", "label": query[:80], "data": {"full": query}})

    # ── Answer node ───────────────────────────────────────────────────────────
    answer_id = "node_answer"
    nodes.append({"id": answer_id, "type": "answer", "label": "Generated Answer", "data": {"text": answer}})
    edges.append({"id": "e_q_a", "source": query_id, "target": answer_id, "label": "generates"})

    # ── Source nodes ─────────────────────────────────────────────────────────
    source_node_map: Dict[str, str] = {}  # chunk_key → node_id
    for p in passages:
        meta = p.get("metadata", {})
        chunk_key = f"{meta.get('doc_id','')}_{meta.get('chunk_index',0)}"
        if chunk_key not in source_node_map:
            node_id = f"node_src_{len(source_node_map)}"
            source_node_map[chunk_key] = node_id
            nodes.append({
                "id": node_id,
                "type": "source",
                "label": meta.get("source_name", "Unknown"),
                "data": {
                    "text": p.get("text", ""),
                    "sentences": p.get("sentences", []),
                    "similarity": p.get("similarity", 0),
                    "rerank_score": p.get("rerank_score", 0),
                    "doc_id": meta.get("doc_id", ""),
                    "chunk_index": meta.get("chunk_index", 0),
                },
            })

    # ── Claim nodes + edges ───────────────────────────────────────────────────
    for i, claim_rec in enumerate(verified_claims):
        claim_id = f"node_claim_{i}"
        nodes.append({
            "id": claim_id,
            "type": "claim",
            "label": claim_rec["claim"][:60] + ("…" if len(claim_rec["claim"]) > 60 else ""),
            "data": {
                "full_claim": claim_rec["claim"],
                "confidence": claim_rec["confidence"],
                "confidence_label": claim_rec["label"],
            },
        })
        edges.append({
            "id": f"e_a_c{i}",
            "source": answer_id,
            "target": claim_id,
            "label": "contains",
        })

        # Link claim → best source sentence
        cit = claim_rec.get("citation", {})
        if cit:
            chunk_key = f"{cit.get('doc_id','')}_{cit.get('chunk_index',0)}"
            src_node = source_node_map.get(chunk_key)
            if src_node:
                edges.append({
                    "id": f"e_c{i}_src",
                    "source": claim_id,
                    "target": src_node,
                    "label": "supported_by",
                    "data": {
                        "grounding_score": cit.get("grounding_score", 0),
                        "sentence": cit.get("sentence", ""),
                        "sentence_index": cit.get("sentence_index", 0),
                    },
                })

    log.info(
        f"Citation graph built",
        extra={"nodes": len(nodes), "edges": len(edges)},
    )
    return {"nodes": nodes, "edges": edges}
