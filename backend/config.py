"""
PolicyPilot – Central Configuration
All tuneable parameters in one place, loaded from environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

# ── LLM ──────────────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
LLM_MODEL: str         = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_MAX_TOKENS: int    = int(os.getenv("LLM_MAX_TOKENS", "2048"))

# ── Vector Store ─────────────────────────────────────────────────────────────
CHROMA_PATH: str    = str(BASE_DIR / "data" / "chroma_db")
COLLECTION_NAME: str = "policy_documents"

# ── Retrieval ─────────────────────────────────────────────────────────────────
EMBEDDING_MODEL: str  = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RERANK_MODEL: str     = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
TOP_K_RETRIEVE: int   = int(os.getenv("TOP_K_RETRIEVE", "10"))
TOP_K_RERANK: int     = int(os.getenv("TOP_K_RERANK", "5"))

# ── CRAG Confidence Thresholds ─────────────────────────────────────────────
CONFIDENCE_HIGH: float = float(os.getenv("CONFIDENCE_HIGH", "0.70"))   # → Correct
CONFIDENCE_LOW:  float = float(os.getenv("CONFIDENCE_LOW",  "0.35"))   # → Incorrect

# ── Self-RAG ──────────────────────────────────────────────────────────────────
MAX_SELF_CORRECTION_LOOPS: int = int(os.getenv("MAX_SELF_CORRECTION_LOOPS", "2"))

# ── File Upload ───────────────────────────────────────────────────────────────
UPLOAD_DIR: str     = str(BASE_DIR / "data" / "uploads")
ALLOWED_EXT: set    = {"pdf", "txt", "docx", "md"}
MAX_FILE_MB: int    = int(os.getenv("MAX_FILE_MB", "50"))

# ── Flask ─────────────────────────────────────────────────────────────────────
SECRET_KEY: str  = os.getenv("SECRET_KEY", "policypilot-dev-secret-change-me")
DEBUG: bool      = os.getenv("FLASK_DEBUG", "false").lower() == "true"
PORT: int        = int(os.getenv("PORT", "5000"))
CORS_ORIGIN: str = os.getenv("CORS_ORIGIN", "http://localhost:3000")
