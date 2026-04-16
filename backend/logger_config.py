"""
PolicyPilot – Centralized Logging Configuration
Every pipeline step, retrieval action, confidence score, and API call is logged
with structured JSON to both console and rotating file handlers.
"""

import logging
import logging.handlers
import json
import time
import os
from pathlib import Path
from functools import wraps

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


class JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Merge any 'extra' keys the caller provided
        for key, val in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "taskName",
            ):
                payload[key] = val
        return json.dumps(payload, default=str)


def _build_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger  # Already configured

    # ── Console handler ──────────────────────────────────────────────────────
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(
        logging.Formatter(
            "%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s",
            datefmt="%H:%M:%S",
        )
    )

    # ── Rotating file handler (JSON) ─────────────────────────────────────────
    fh = logging.handlers.RotatingFileHandler(
        LOG_DIR / "policypilot.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(JSONFormatter())

    logger.addHandler(ch)
    logger.addHandler(fh)
    logger.propagate = False
    return logger


# ── Public loggers ────────────────────────────────────────────────────────────
app_log        = _build_logger("policypilot.app")
pipeline_log   = _build_logger("policypilot.pipeline")
retriever_log  = _build_logger("policypilot.retriever")
reranker_log   = _build_logger("policypilot.reranker")
fact_log       = _build_logger("policypilot.factcheck")
confidence_log = _build_logger("policypilot.confidence")
graph_log      = _build_logger("policypilot.graph")
route_log      = _build_logger("policypilot.routes")


# ── Decorator: log execution time of any function ────────────────────────────
def log_step(logger: logging.Logger, step_name: str):
    """Decorator that logs entry, exit, and elapsed time for a pipeline step."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            logger.info(f"▶ START  {step_name}")
            t0 = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                elapsed = (time.perf_counter() - t0) * 1000
                logger.info(f"✓ END    {step_name}  ({elapsed:.1f} ms)")
                return result
            except Exception as exc:
                elapsed = (time.perf_counter() - t0) * 1000
                logger.exception(
                    f"✗ ERROR  {step_name}  ({elapsed:.1f} ms)", exc_info=exc
                )
                raise
        return wrapper
    return decorator
