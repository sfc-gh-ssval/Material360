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
├── sql/                      # Snowflake DDL + seed + sample load (run in order)
└── .env.example              # Connection / warehouse settings template
```

## Snowflake Objects

All objects live in `SNOWFLAKE_INTELLIGENCE.ENGINEERING_DRAWINGS` and are defined in [`sql/`](sql):

| Script | Creates | Purpose |
|--------|---------|---------|
| `00_setup.sql` | Database, schema, optional `MATERIAL360_WH` | Container + compute |
| `01_stage_and_tables.sql` | `DRAWING_STAGE`, `DRAWING_EXTRACTIONS`, `BOM_PARTS` | Drawing files (SSE + directory table), extracted metadata, BOM master |
| `02_views.sql` | `V_BOM_RECONCILIATION` | Drawing ↔ BOM reconciliation (resolved value + source) |
| `03_procedure.sql` | `EXTRACT_DRAWING(file_name)` | AI_COMPLETE vision extraction → row in `DRAWING_EXTRACTIONS` |
| `04_search_service.sql` | `DRAWING_SEARCH` | Cortex Search over `SEARCH_TEXT` for Agent Chat |
| `05_seed_bom.sql` | Rows in `BOM_PARTS` | Sample BOM for the 7 synthetic drawings |
| `06_load_synthetic_drawings.sql` | Rows in `DRAWING_EXTRACTIONS` | Uploads + extracts the sample PDFs |

Scripts 00–05 are idempotent (`IF NOT EXISTS` for stage/tables/search service; the view and procedure are `CREATE OR REPLACE`). Script 06 inserts a new extraction row each time it runs.

### Deploy

Set the warehouse in `04_search_service.sql` (default `MATERIAL360_WH`), then run from the repo root:

```bash
for f in sql/0*.sql; do
  snow sql -c <connection> --enable-templating NONE -f "$f"
done
```

`--enable-templating NONE` is required: the extraction prompt contains `GD&T`, which Snowflake CLI otherwise treats as a `&T` variable. Scripts 00–05 can also be run in a Snowsight worksheet; 06 needs a client for `PUT` (or use the app's Upload page).

The role used needs `SNOWFLAKE.CORTEX_USER` and access to `claude-sonnet-4-6` in your region (or cross-region inference enabled).
