"""
PolicyPilot – Flask Application Entry Point
"""

from __future__ import annotations

import time
from flask import Flask, jsonify, request
from flask_cors import CORS

import config
from logger_config import app_log as log
from routes import query_bp, doc_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY

    # ── CORS ────────────────────────────────────────────────────────────────
    CORS(app, origins=[config.CORS_ORIGIN, "http://localhost:3000", "http://localhost:5173"])

    # ── Blueprints ───────────────────────────────────────────────────────────
    app.register_blueprint(query_bp)
    app.register_blueprint(doc_bp)

    # ── Request logging middleware ───────────────────────────────────────────
    @app.before_request
    def _before():
        request._start_time = time.perf_counter()
        log.info(
            f"→ {request.method} {request.path}",
            extra={"ip": request.remote_addr},
        )

    @app.after_request
    def _after(response):
        elapsed = (time.perf_counter() - getattr(request, "_start_time", time.perf_counter())) * 1000
        log.info(
            f"← {response.status_code} {request.path}  ({elapsed:.1f} ms)",
            extra={"status": response.status_code, "ms": round(elapsed, 1)},
        )
        return response

    # ── Health check ─────────────────────────────────────────────────────────
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "PolicyPilot"}), 200

    # ── Error handlers ────────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        log.exception("Unhandled 500", exc_info=e)
        return jsonify({"error": "Internal server error"}), 500

    log.info(
        f"PolicyPilot Flask app created",
        extra={"debug": config.DEBUG, "port": config.PORT},
    )
    return app


if __name__ == "__main__":
    app = create_app()
    log.info(f"Starting PolicyPilot on port {config.PORT}")
    app.run(host="0.0.0.0", port=config.PORT, debug=config.DEBUG)
