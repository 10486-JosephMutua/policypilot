"""
PolicyPilot – Retriever
Handles document ingestion, sentence-level chunking, embedding, and retrieval
from ChromaDB. Every passage is stored with sentence-level span metadata so
we can later trace an answer claim back to its exact source sentence.
"""

from __future__ import annotations

import re
import uuid
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from logger_config import retriever_log as log, log_step
import config


# ── Sentence splitter ─────────────────────────────────────────────────────────
_SENT_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')

def _split_sentences(text: str) -> List[str]:
    """Split text into sentences, preserving a minimum character length."""
    raw = _SENT_RE.split(text.strip())
    out: List[str] = []
    buf = ""
    for s in raw:
        buf = (buf + " " + s).strip() if buf else s
        if len(buf) >= 80:
            out.append(buf)
            buf = ""
    if buf:
        out.append(buf)
    return out


def _sliding_window_chunks(
    sentences: List[str],
    window: int = 5,
    stride: int = 2,
) -> List[Dict[str, Any]]:
    """
    Build overlapping windows of `window` sentences with a stride of `stride`.
    Each chunk records the exact sentence indices so we can reconstruct citations.
    """
    chunks: List[Dict[str, Any]] = []
    i = 0
    while i < len(sentences):
        span = sentences[i : i + window]
        chunks.append(
            {
                "text": " ".join(span),
                "start_idx": i,
                "end_idx": min(i + window, len(sentences)) - 1,
                "sentences": span,
            }
        )
        i += stride
        if i >= len(sentences):
            break
    return chunks


# ── Embedder singleton ────────────────────────────────────────────────────────
class _Embedder:
    _instance: Optional["_Embedder"] = None

    def __init__(self):
        log.info(f"Loading embedding model: {config.EMBEDDING_MODEL}")
        self._model = SentenceTransformer(config.EMBEDDING_MODEL)

    @classmethod
    def get(cls) -> "_Embedder":
        if cls._instance is None:
            cls._instance = _Embedder()
        return cls._instance

    def encode(self, texts: List[str]) -> List[List[float]]:
        return self._model.encode(texts, convert_to_numpy=True).tolist()


# ── ChromaDB client ───────────────────────────────────────────────────────────
def _get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(
        path=config.CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(
        config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ── Public API ─────────────────────────────────────────────────────────────────
@log_step(log, "ingest_document")
def ingest_document(
    text: str,
    source_name: str,
    doc_type: str = "policy",
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Ingest a document: split into sentence windows, embed, and store in ChromaDB.
    Returns the document_id.
    """
    doc_id = hashlib.sha256(text.encode()).hexdigest()[:16]
    log.info(f"Ingesting document", extra={"doc_id": doc_id, "source": source_name})

    sentences = _split_sentences(text)
    log.debug(f"Split into {len(sentences)} sentences")

    chunks = _sliding_window_chunks(sentences)
    log.debug(f"Created {len(chunks)} sliding-window chunks")

    collection = _get_collection()
    embedder = _Embedder.get()

    texts_to_embed = [c["text"] for c in chunks]
    embeddings = embedder.encode(texts_to_embed)

    ids, docs, metas, embeds = [], [], [], []
    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        chunk_id = f"{doc_id}__c{idx}"
        meta = {
            "doc_id": doc_id,
            "source_name": source_name,
            "doc_type": doc_type,
            "chunk_index": idx,
            "start_sentence_idx": chunk["start_idx"],
            "end_sentence_idx": chunk["end_idx"],
            "sentences_json": "|||".join(chunk["sentences"]),
            **(extra_metadata or {}),
        }
        ids.append(chunk_id)
        docs.append(chunk["text"])
        metas.append(meta)
        embeds.append(emb)

    # Upsert in batches of 100
    batch = 100
    for i in range(0, len(ids), batch):
        collection.upsert(
            ids=ids[i:i+batch],
            documents=docs[i:i+batch],
            metadatas=metas[i:i+batch],
            embeddings=embeds[i:i+batch],
        )

    log.info(
        f"Ingestion complete",
        extra={"doc_id": doc_id, "chunks": len(chunks)},
    )
    return doc_id


@log_step(log, "retrieve_passages")
def retrieve_passages(
    query: str,
    top_k: int = config.TOP_K_RETRIEVE,
) -> List[Dict[str, Any]]:
    """
    Retrieve the top-k most semantically similar passages for a query.
    Returns a list of passage dicts with text, metadata, and similarity score.
    """
    log.info(f"Retrieving passages", extra={"query": query[:80], "top_k": top_k})
    embedder = _Embedder.get()
    query_emb = embedder.encode([query])[0]

    collection = _get_collection()
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=min(top_k, collection.count() or 1),
        include=["documents", "metadatas", "distances"],
    )

    passages = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        similarity = 1.0 - dist  # cosine distance → similarity
        passages.append(
            {
                "text": doc,
                "metadata": meta,
                "similarity": round(similarity, 4),
                "sentences": meta.get("sentences_json", "").split("|||"),
            }
        )

    log.info(
        f"Retrieved {len(passages)} passages",
        extra={"top_sim": passages[0]["similarity"] if passages else 0},
    )
    return passages


def list_documents() -> List[Dict[str, Any]]:
    """Return distinct documents in the store."""
    collection = _get_collection()
    if collection.count() == 0:
        return []

    results = collection.get(include=["metadatas"])
    seen: Dict[str, Dict] = {}
    for meta in results["metadatas"]:
        did = meta.get("doc_id", "")
        if did and did not in seen:
            seen[did] = {
                "doc_id": did,
                "source_name": meta.get("source_name", "Unknown"),
                "doc_type": meta.get("doc_type", "policy"),
            }
    return list(seen.values())


def document_count() -> int:
    return _get_collection().count()
