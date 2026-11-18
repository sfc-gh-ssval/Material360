# Material360

Engineering drawing intelligence platform built on Snowflake Cortex AI. Extracts structured metadata from multilingual engineering drawings using vision models, indexes them for semantic search, and provides a RAG-powered agent chat for natural language queries.

## Features

- **Document Extraction** — Upload engineering drawings (PDF) and extract title block data, dimensions, BOM, materials using Cortex AI vision (claude-sonnet-4-6)
- **Multilingual Support** — Detects source language (Italian, German, French, Spanish, English) and translates all fields to English
- **Agent Chat** — Ask natural language questions about drawings using RAG (Cortex Search + AI_COMPLETE)
- **BOM Reconciliation** — Cross-reference extracted BOM data against drawing metadata
- **Document Preview** — Inline PDF viewer for uploaded drawings

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full architecture document and diagrams.

```
Frontend (React 19 + Vite 8)
    │  Axios → Vite proxy /api → :8000
Backend (FastAPI + Uvicorn)
    │  Snowpark session (OAuth)
Snowflake (SNOWFLAKE_INTELLIGENCE.ENGINEERING_DRAWINGS)
    ├── @DRAWING_STAGE (PDFs)
    ├── DRAWING_EXTRACTIONS (30+ columns)
    ├── BOM_PARTS
    ├── V_BOM_RECONCILIATION
    ├── EXTRACT_DRAWING() stored procedure
    ├── DRAWING_SEARCH (Cortex Search service)
    └── AI_COMPLETE (claude-sonnet-4-6 for vision extraction and chat)
```

## Prerequisites

- Python 3.12+ (conda recommended)
- Node.js 18+
- Snowflake account with Cortex AI enabled
- `~/.snowflake/connections.toml` with an OAuth connection configured:

```toml
[my_connection]
account = "YOUR_ACCOUNT"
user = "YOUR_USER"
authenticator = "oauth_authorization_code"
client_store_temporary_credential = true
```

Then copy `.env.example` to `.env` and set `SNOWFLAKE_CONNECTION_NAME` (e.g. `my_connection`) and `SNOWFLAKE_WAREHOUSE`.

## Quick Start

```bash
# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..

# Start backend (opens browser for OAuth on first run)
PYTHONPATH=$PWD python -m uvicorn backend.main:app --reload --port 8000

# In another terminal — start frontend
cd frontend && npm run dev
```

Open http://localhost:5173

## Project Structure

```
Material360/
├── backend/
│   ├── main.py              # FastAPI app with lifespan auth
│   ├── config.py             # Snowflake settings
│   ├── routers/
│   │   ├── upload.py         # POST /api/upload
│   │   ├── results.py        # GET /api/extractions, /api/reconciliation, /api/bom
│   │   ├── files.py          # GET /api/files/:f/preview
│   │   └── agent.py          # POST /api/agent/chat, /api/agent/search
│   ├── services/
│   │   ├── snowflake.py      # Snowpark session with auto-reconnect
│   │   └── extraction.py     # AI extraction, Cortex Search, RAG agent
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Router + sidebar nav
│   │   ├── pages/
│   │   │   ├── Drawings.tsx  # Drawing list + detail view
│   │   │   ├── Upload.tsx    # Drag-and-drop upload
│   │   │   ├── Reconciliation.tsx  # BOM cross-reference
│   │   │   ├── AgentChat.tsx # RAG chat interface
│   │   │   └── Architecture.tsx  # In-app architecture page
│   │   ├── services/api.ts   # API client
│   │   └── stores/uploadStore.ts  # Upload state management
│   └── vite.config.ts        # Proxy /api → :8000
├── synthetic_drawings/       # 7 test PDFs + generator script + ground truth
├── cortex-agent-clarification/  # Reusable Cortex Agent SSE/clarification component
├── docs/                     # Architecture docs + SVG diagrams
└── .env.example              # Connection / warehouse settings template
```

## Snowflake Objects Required

These must exist in `SNOWFLAKE_INTELLIGENCE.ENGINEERING_DRAWINGS`:

| Object | Type | Purpose |
|--------|------|---------|
| `DRAWING_STAGE` | Stage | PDF file storage |
| `DRAWING_EXTRACTIONS` | Table | Extracted metadata (30+ columns) |
| `BOM_PARTS` | Table | Bill of materials entries |
| `V_BOM_RECONCILIATION` | View | Drawing-to-BOM cross-reference |
| `EXTRACT_DRAWING` | Stored Procedure | Calls AI_COMPLETE with vision to parse PDFs |
| `DRAWING_SEARCH` | Cortex Search Service | Semantic search over SEARCH_TEXT column |
