# PolicyPilot — Hallucination-Proof Legal & Compliance RAG

> Week 10 of the 12-Week AI Sprint

## What Makes This Different

| Feature | Standard RAG | PolicyPilot |
|---------|-------------|-------------|
| Confidence scoring | ❌ | ✅ Tri-layer CRAG scoring |
| Claim-level verification | ❌ | ✅ FactChecker decomposition |
| Sentence-level citations | ❌ | ✅ Exact sentence anchoring |
| Self-correction loop | ❌ | ✅ Self-RAG + LangGraph |
| Citation provenance graph | ❌ | ✅ D3 interactive graph |
| Temporal hallucination flags | ❌ | ✅ Year-reference detection |

## Architecture

```
User Query
    │
    ▼
[LangGraph State Machine]
    ├── Retrieve (ChromaDB cosine)
    ├── Re-rank (Cross-Encoder ms-marco)
    ├── CRAG Assess ─┬─ Correct   → Generate (confident)
    │               ├─ Ambiguous → Generate (cautious)
    │               └─ Incorrect → Reformulate → loop
    ├── Generate (Claude + grounded prompting)
    ├── Verify Claims (FactChecker decomposition)
    └── Build Citation Graph
```

## Research Foundations

- **CRAG** (Shi et al., 2024) — arxiv 2401.15884 — Corrective Retrieval with confidence thresholds
- **Self-RAG** (Asai et al., 2023) — arxiv 2310.11511 — Reflection tokens (IsRel/IsSup/IsUse)
- **HalluDetect** (2025) — FactChecker pattern: decompose claims → verify each → synthesise
- **Hallucination-Free?** (Stanford, 2025) — Legal RAG hallucination taxonomy (correctness / groundedness)

## Quick Start

### Backend
```bash
cd backend
cp .env.example .env
# Add your GROQ_API_KEY to .env
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd frontend
cp .env.example .env
npm install
npm start
```

Open http://localhost:3000

## Logging

All pipeline steps log to:
- **Console** (INFO level, human-readable)
- **`backend/logs/policypilot.log`** (DEBUG level, structured JSON, rotating 10 MB × 5)

Every log entry includes: timestamp, level, logger name, function, line, and step-specific extras (confidence scores, query text, elapsed ms).

## File Structure
```
PolicyPilot/
├── backend/
│   ├── app.py                      # Flask entry point
│   ├── config.py                   # All configuration
│   ├── logger_config.py            # Centralized JSON logging
│   ├── requirements.txt
│   ├── pipeline/
│   │   ├── crag_pipeline.py        # LangGraph CRAG + Self-RAG orchestration
│   │   ├── retriever.py            # ChromaDB ingestion & retrieval
│   │   ├── reranker.py             # Cross-encoder re-ranking
│   │   ├── confidence_scorer.py    # Tri-layer confidence scoring
│   │   └── citation_graph.py      # Provenance graph builder
│   ├── routes/
│   │   ├── query_routes.py         # /api/query  /api/challenge
│   │   └── document_routes.py     # /api/documents/*
│   └── utils/
│       └── text_utils.py          # PDF/DOCX/TXT extraction
└── frontend/
    └── src/
        ├── App.jsx
        ├── components/
        │   ├── ConfidenceGauge.jsx  # SVG arc gauge
        │   ├── ClaimVerifier.jsx    # Per-claim audit list
        │   ├── CitationGraph.jsx    # D3 provenance graph
        │   ├── SourcePanel.jsx      # Source passage explorer
        │   ├── QueryPanel.jsx       # Search + challenge UI
        │   ├── ResultPanel.jsx      # Tabbed results view
        │   └── Sidebar.jsx          # Document management
        └── services/api.js
```
