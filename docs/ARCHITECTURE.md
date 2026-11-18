# Material360 — Solution Architecture

## System Overview

Material360 is a full-stack engineering drawing intelligence platform that extracts structured metadata from multilingual engineering drawings using Snowflake Cortex AI vision models, indexes them for semantic search, and exposes a RAG-powered agent chat for natural language queries.

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React SPA)                        │
│   Vite 8 · React 19 · TypeScript 6 · react-router-dom 7           │
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌───────────────┐ ┌──────────────────┐  │
│  │ Drawings │ │  Upload  │ │Reconciliation │ │   Agent Chat     │  │
│  │  List +  │ │ Drag/Drop│ │  BOM vs Dwg   │ │ RAG Q&A + GFM   │  │
│  │  Detail  │ │ Progress │ │  Cross-Ref    │ │ Markdown Tables  │  │
│  └────┬─────┘ └────┬─────┘ └──────┬────────┘ └───────┬──────────┘  │
│       │             │              │                  │             │
│       └─────────────┴──────────────┴──────────────────┘             │
│                         api.ts (Axios)                              │
│                    Vite proxy /api → :8000                          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP
┌──────────────────────────────▼──────────────────────────────────────┐
│                      BACKEND (FastAPI + Uvicorn)                    │
│                                                                     │
│  ┌─────────────────────────── Routers ──────────────────────────┐   │
│  │  POST /api/upload      → PUT to stage + CALL EXTRACT_DRAWING │   │
│  │  GET  /api/extractions → SELECT from DRAWING_EXTRACTIONS     │   │
│  │  GET  /api/reconciliation → SELECT from V_BOM_RECONCILIATION │   │
│  │  GET  /api/bom         → SELECT from BOM_PARTS               │   │
│  │  GET  /api/files/:f/preview → GET from @DRAWING_STAGE        │   │
│  │  POST /api/agent/chat  → Cortex Search + AI_COMPLETE (RAG)   │   │
│  │  POST /api/agent/search → Cortex Search direct query         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌── Services ──────────────────────────────────────────────────┐   │
│  │  snowflake.py  → Snowpark session (OAuth, auto-reconnect)   │   │
│  │  extraction.py → EXTRACT_DRAWING, search_drawings, agent_chat│   │
│  └──────────────────────────────────────────────────────────────┘   │
│  config.py → Settings (DB, schema, stage, search svc, model)       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ Snowpark / SQL
┌──────────────────────────────▼──────────────────────────────────────┐
│                    SNOWFLAKE (SNOWFLAKE_INTELLIGENCE)                │
│                    Schema: ENGINEERING_DRAWINGS                      │
│                    Warehouse: <your warehouse>                       │
│                                                                     │
│  ┌─── Storage ────────────────────────────────────────────────┐     │
│  │  @DRAWING_STAGE          PDF / image drawing files          │     │
│  │  DRAWING_EXTRACTIONS     Extracted metadata (30+ columns)   │     │
│  │  BOM_PARTS               Bill of materials entries          │     │
│  │  V_BOM_RECONCILIATION    View: drawing ↔ BOM cross-ref     │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌─── AI Services ────────────────────────────────────────────┐     │
│  │                                                             │     │
│  │  EXTRACT_DRAWING(filename)                                  │     │
│  │  └─ AI_COMPLETE(claude-sonnet-4-6, vision)                  │     │
│  │     └─ Reads PDF from @DRAWING_STAGE                        │     │
│  │     └─ 46-line system prompt (multilingual, structured JSON)│     │
│  │     └─ Outputs: part#, material, dims, BOM, translations    │     │
│  │                                                             │     │
│  │  DRAWING_SEARCH (Cortex Search Service)                     │     │
│  │  └─ Source: DRAWING_EXTRACTIONS.SEARCH_TEXT                  │     │
│  │  └─ Auto-refreshing index over all extraction records       │     │
│  │  └─ Queried via SEARCH_PREVIEW() in agent_chat()            │     │
│  │                                                             │     │
│  │  AI_COMPLETE (Agent Chat - RAG pattern)                     │     │
│  │  └─ Step 1: Cortex Search retrieval (top-5 results)         │     │
│  │  └─ Step 2: Context assembly from SEARCH_TEXT               │     │
│  │  └─ Step 3: AI_COMPLETE with claude-sonnet-4-6              │     │
│  │  └─ Structured prompt: compare, tabulate, cite sources      │     │
│  └─────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Document Ingestion

```
User drops PDF ──► POST /api/upload
                       │
                       ├─ 1. Write to temp file
                       ├─ 2. PUT file → @DRAWING_STAGE
                       ├─ 3. CALL EXTRACT_DRAWING(filename)
                       │       │
                       │       ├─ BUILD_SCOPED_FILE_URL(@DRAWING_STAGE, file)
                       │       ├─ AI_COMPLETE(claude-sonnet-4-6, vision)
                       │       │   └─ System prompt: extract title block, dims,
                       │       │     BOM, materials, detect language, translate
                       │       ├─ Parse JSON response → INSERT DRAWING_EXTRACTIONS
                       │       └─ Parse BOM array → INSERT BOM_PARTS
                       │
                       └─ 4. Return extraction result to frontend
                                │
                       Cortex Search auto-refreshes DRAWING_SEARCH
                       index from updated SEARCH_TEXT column
```

---

## Data Flow: Agent Chat (RAG)

```
User asks question ──► POST /api/agent/chat
                           │
                           ├─ 1. SEARCH_PREVIEW('DRAWING_SEARCH', query)
                           │     └─ Returns top-5 matching SEARCH_TEXT chunks
                           │
                           ├─ 2. Build context string from search results
                           │     └─ "Drawing 1: {SEARCH_TEXT}\nDrawing 2: ..."
                           │
                           ├─ 3. AI_COMPLETE(claude-sonnet-4-6)
                           │     └─ System: "You are Material360 assistant..."
                           │     └─ User: context + original question
                           │     └─ Instructions: tables, comparisons, cite sources
                           │
                           └─ 4. Return markdown response → rendered with
                                  react-markdown + remark-gfm (tables, lists)
```

---

## DRAWING_EXTRACTIONS Schema (30+ columns)

| Column Group | Fields |
|---|---|
| **Identity** | EXTRACTION_ID, FILE_NAME, FILE_PATH, EXTRACTION_TIMESTAMP, MODEL_USED |
| **Classification** | DRAWING_TYPE, SOURCE_LANGUAGE, SOURCE_LANGUAGE_NAME, WAS_TRANSLATED |
| **Part Info** | PART_NUMBER, PART_NAME, ORIGINAL_PART_NAME, REVISION |
| **Materials** | MATERIAL, FINISH, ORIGINAL_FINISH, COSMETIC_REQUIREMENT |
| **People** | DESIGNER, DRAFTSMAN |
| **Physical** | WEIGHT_KG, BBOX_X, BBOX_Y, BBOX_Z, BBOX_SOURCE |
| **Quality** | MISSING_FIELDS (array), CRITICAL_DIMENSIONS (JSON array) |
| **BOM** | BOM (translated JSON), ORIGINAL_BOM (source language JSON) |
| **Search** | SEARCH_TEXT (denormalized text for Cortex Search indexing) |
| **Raw** | RAW_RESPONSE, PARSED (boolean) |

---

## SEARCH_TEXT Construction

```
Part: TLS-IT-90200 | Welded Frame for Electrical Panel |
TELAIO SALDATO PER QUADRO ELETTRICO | Rev 01 | Material: S235JR |
Finish: Painting RAL 7035 | VERNICIATURA RAL 7035 |
Weight: 45.8 kg | Language: Italian
```

Pipe-delimited, includes both translated and original terms for multilingual retrieval.

---

## Frontend Pages

| Page | Route | Purpose |
|---|---|---|
| **Drawings** | `/` | Split-panel list + detail. 4 tabs: Document preview (iframe), Extraction grid, BOM table, Raw JSON. Field completeness indicator. Search/filter. |
| **Upload** | `/upload` | Drag-and-drop zone. Real-time progress via `uploadStore` (uploading → extracting → done). Sidebar widget shows active jobs. |
| **Reconciliation** | `/reconciliation` | BOM cross-reference table. Source badges (Drawing/BOM/Missing). Material and finish comparison. |
| **Agent Chat** | `/chat` | Session-persistent message history. Markdown rendering with GFM tables. Newest-first display. |

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | React + TypeScript | 19.2 / 6.0 |
| Build | Vite | 8.3 |
| Routing | react-router-dom | 7.18 |
| HTTP Client | Axios | 1.20 |
| Markdown | react-markdown + remark-gfm | 10.1 / 4.0 |
| Backend | FastAPI + Uvicorn | 0.115 / 0.30 |
| Session Mgmt | Snowpark Python | via snowflake-connector 3.12 |
| Auth | OAuth authorization_code | Token cached locally |
| Vision Model | claude-sonnet-4-6 | Snowflake Cortex |
| Chat Model | claude-sonnet-4-6 | Snowflake Cortex |
| Search | Cortex Search (DRAWING_SEARCH) | Serverless |
| Warehouse | Configurable (`SNOWFLAKE_WAREHOUSE`) | |
| Database | SNOWFLAKE_INTELLIGENCE | ENGINEERING_DRAWINGS schema |

---

## Cost Drivers

| Category | Service | Notes |
|---|---|---|
| Ingestion | AI_COMPLETE (vision) + warehouse | One call per drawing; larger multi-sheet PDFs consume more tokens |
| Search indexing | DRAWING_SEARCH | Embedding on refresh; small at demo scale |
| Agent Chat | Cortex Search + AI_COMPLETE | Per question |

---

## Drawings Inventory

The repo ships 7 synthetic test drawings in `synthetic_drawings/` (generated by `generate_drawings.py`, with `ground_truth.json`). Load your own drawings to the stage for real data.

| File | Language | Part | Source |
|---|---|---|---|
| EN_bracket_assy.pdf | English | Bracket Assembly | Synthetic |
| EN_shaft_adapter.pdf | English | Shaft Adapter | Synthetic |
| EN_sensor_mount_degraded.pdf | English | Sensor Mount (degraded scan) | Synthetic |
| DE_kabelrinne_platte.pdf | German | Cable Tray Plate | Synthetic |
| FR_gousset.pdf | French | Gusset Plate | Synthetic |
| IT_telaio_saldato.pdf | Italian | Welded Frame | Synthetic |
| ES_placa_cubierta.pdf | Spanish | Cover Plate | Synthetic |

---

## Getting Started

### Prerequisites
- Python 3.12+ with conda
- Node.js 18+
- Snowflake account with Cortex AI enabled
- `~/.snowflake/connections.toml` with an OAuth connection, referenced via `SNOWFLAKE_CONNECTION_NAME` (see `.env.example`)

### Start the App
```bash
# Terminal 1 — Backend (will open browser for OAuth on first run)
cd Material360
PYTHONPATH=$PWD python -m uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
cd Material360/frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.
