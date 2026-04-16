"""
PolicyPilot – Document Routes
POST /api/documents/upload   – ingest a document
GET  /api/documents          – list all documents
GET  /api/documents/count    – document chunk count
"""

from __future__ import annotations

import os
from pathlib import Path

from flask import Blueprint, request, jsonify

from logger_config import route_log as log
from pipeline.retriever import ingest_document, list_documents, document_count
from utils.text_utils import extract_text
import config

doc_bp = Blueprint("documents", __name__)


@doc_bp.post("/api/documents/upload")
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "No file in request"}), 400

    f = request.files["file"]
    
    # --- FIX START ---
    # Read the content once into memory
    raw = f.read() 
    file_size = len(raw)
    # -----------------

    print(f"Received file: {f.filename}, content_type: {f.content_type}, size: {file_size} bytes")
    
    filename = f.filename or "upload"
    ext = Path(filename).suffix.lower().lstrip(".")

    if ext not in config.ALLOWED_EXT:
        return jsonify({"error": f"Unsupported file type: .{ext}"}), 400

    # Use the variable 'file_size' instead of reading again
    mb = file_size / (1024 * 1024)
    if mb > config.MAX_FILE_MB:
        return jsonify({"error": f"File too large ({mb:.1f} MB > {config.MAX_FILE_MB} MB)"}), 400

    # Use the variable 'raw' which now actually contains the data
    text = extract_text(raw, filename)
    
    if not text or not text.strip():
        print("Could not extract text from file")
        return jsonify({"error": "Could not extract text from file"}), 422

    # Save original to disk using the 'raw' variable
    save_path = Path(config.UPLOAD_DIR) / filename
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(raw)

    # ... rest of your code
    doc_type = request.form.get("doc_type", "policy")
    print(f"Extracted text length: {len(text)} characters")
    doc_id = ingest_document(
        text,
        source_name=filename,
        doc_type=doc_type,
        extra_metadata={"original_filename": filename},
    )

    return jsonify({
        "doc_id":      doc_id,
        "source_name": filename,
        "doc_type":    doc_type,
        "size_mb":     round(mb, 2),
        "text_length": len(text),
    }), 201


@doc_bp.get("/api/documents")
def get_documents():
    docs = list_documents()
    return jsonify({"documents": docs, "total": len(docs)}), 200


@doc_bp.get("/api/documents/count")
def get_count():
    return jsonify({"count": document_count()}), 200


@doc_bp.post("/api/documents/ingest-text")
def ingest_raw_text():
    """Ingest plain text directly (for demo seeding)."""
    data = request.get_json(silent=True) or {}
    text        = (data.get("text") or "").strip()
    source_name = (data.get("source_name") or "Manual Input").strip()
    doc_type    = (data.get("doc_type") or "policy").strip()

    if not text:
        return jsonify({"error": "text is required"}), 400

    doc_id = ingest_document(text, source_name=source_name, doc_type=doc_type)
    return jsonify({"doc_id": doc_id, "source_name": source_name}), 201
