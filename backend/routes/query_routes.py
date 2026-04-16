"""
PolicyPilot – Query Routes
POST /api/query        – run the full CRAG pipeline
POST /api/challenge    – challenge an answer (re-research loop)
"""

from __future__ import annotations

from flask import Blueprint, request, jsonify
from logger_config import route_log as log
from pipeline.crag_pipeline import run_pipeline

query_bp = Blueprint("query", __name__)


@query_bp.post("/api/query")
def handle_query():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()

    if not query:
        return jsonify({"error": "query is required"}), 400

    log.info(f"POST /api/query", extra={"query": query[:80]})

    try:
        result = run_pipeline(query)
        return jsonify(result), 200
    except Exception as exc:
        log.exception("Pipeline error", exc_info=exc)
        return jsonify({"error": str(exc)}), 500


@query_bp.post("/api/challenge")
def handle_challenge():
    """
    Re-research endpoint.  The frontend submits the original query +
    an optional challenge reason so the pipeline can refine its answer.
    """
    data = request.get_json(silent=True) or {}
    query   = (data.get("query") or "").strip()
    reason  = (data.get("reason") or "").strip()

    if not query:
        return jsonify({"error": "query is required"}), 400

    log.info(
        f"POST /api/challenge",
        extra={"query": query[:80], "reason": reason[:80]},
    )

    try:
        result = run_pipeline(
            query,
            is_challenge=True,
            challenge_context=reason,
        )
        result["challenged"] = True
        return jsonify(result), 200
    except Exception as exc:
        log.exception("Challenge pipeline error", exc_info=exc)
        return jsonify({"error": str(exc)}), 500
