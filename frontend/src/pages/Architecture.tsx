const LAYERS = [
  {
    key: "frontend",
    title: "Frontend",
    sub: "React + TypeScript · Vite (:5173)",
    items: [
      { name: "Drawings", desc: "List + detail tabs (Document, Extraction, BOM, Raw JSON)" },
      { name: "Upload", desc: "Drag & drop PDF / PNG / JPG / TIFF" },
      { name: "BOM Reconciliation", desc: "Single source of truth grid" },
      { name: "Agent Chat", desc: "Natural-language Q&A over drawings" },
    ],
    note: "services/api.ts  ·  Vite proxy /api/* → :8000",
  },
  {
    key: "backend",
    title: "Backend",
    sub: "FastAPI + Snowpark (:8000)",
    items: [
      { name: "routers/upload.py", desc: "POST /api/upload" },
      { name: "routers/results.py", desc: "/api/extractions · /api/reconciliation · /api/bom" },
      { name: "routers/files.py", desc: "/api/files/{filename}/preview" },
      { name: "routers/agent.py", desc: "/api/agent/chat · /api/agent/search" },
    ],
    note: "services/snowflake.py — single session, health ping, auto-reconnect · OAuth via connections.toml",
  },
  {
    key: "snowflake",
    title: "Snowflake",
    sub: "SNOWFLAKE_INTELLIGENCE.ENGINEERING_DRAWINGS",
    items: [
      { name: "@DRAWING_STAGE", desc: "Raw drawing files" },
      { name: "EXTRACT_DRAWING()", desc: "AI_COMPLETE vision → structured JSON" },
      { name: "DRAWING_EXTRACTIONS", desc: "One row per drawing" },
      { name: "V_BOM_RECONCILIATION", desc: "Extractions ⟕ BOM_PARTS" },
      { name: "DRAWING_SEARCH", desc: "Cortex Search (arctic-embed-m-v1.5)" },
    ],
    note: "All data, embeddings and LLM inference stay inside Snowflake",
  },
];

const FLOWS = [
  {
    title: "A. Ingestion & Extraction",
    tag: "Upload tab",
    steps: [
      "Browser posts file to POST /api/upload",
      "Extension validated; file PUT to @DRAWING_STAGE; stage directory refreshed",
      "CALL EXTRACT_DRAWING(file_name)",
      "AI_COMPLETE('claude-sonnet-4-6', prompt, TO_FILE(stage, file)) — one multimodal call: language detection, translation, title block, dimensions & GD&T, bounding box, missing fields, BOM",
      "TRY_PARSE_JSON → typed columns → INSERT into DRAWING_EXTRACTIONS",
      "Extraction JSON returned; drawing appears in the list",
    ],
  },
  {
    title: "B. Browse & Reconcile",
    tag: "Drawings · BOM Reconciliation",
    steps: [
      "GET /api/extractions — list with language / missing-field filters",
      "GET /api/extractions/{id} — full detail",
      "GET /api/files/{filename}/preview — file pulled from stage, served inline to the Document tab",
      "GET /api/reconciliation — reads V_BOM_RECONCILIATION",
      "Resolved value = COALESCE(drawing, BOM); source = From drawing · Filled from BOM · MISSING",
    ],
  },
  {
    title: "C. Agent Chat (RAG)",
    tag: "Agent Chat",
    steps: [
      "POST /api/agent/chat { question }",
      "Retrieve: CORTEX.SEARCH_PREVIEW('DRAWING_SEARCH', top 5)",
      "Assemble context: part, material, finish, language, dimensions, BOM, bbox, weight, missing fields",
      "Generate: AI_COMPLETE('claude-sonnet-4-6', grounded prompt)",
      "Markdown answer (tables + cited part numbers) rendered in chat",
    ],
  },
];

const AI_FUNCTIONS = [
  { cap: "Drawing extraction", fn: "AI_COMPLETE + TO_FILE", model: "claude-sonnet-4-6", where: "EXTRACT_DRAWING procedure" },
  { cap: "Embeddings", fn: "Cortex Search (auto-embedded)", model: "snowflake-arctic-embed-m-v1.5", where: "DRAWING_SEARCH on SEARCH_TEXT, 1h target lag" },
  { cap: "Retrieval", fn: "SNOWFLAKE.CORTEX.SEARCH_PREVIEW", model: "Hybrid vector + keyword", where: "backend/services/extraction.py" },
  { cap: "Answer generation", fn: "AI_COMPLETE", model: "claude-sonnet-4-6", where: "backend/services/extraction.py" },
];

const OBJECTS = [
  { name: "DRAWING_STAGE", type: "Internal stage", purpose: "Original PDF / image files" },
  { name: "EXTRACT_DRAWING(file_name)", type: "SQL stored procedure", purpose: "Vision extraction, JSON parse, insert" },
  { name: "DRAWING_EXTRACTIONS", type: "Table", purpose: "Title block, language, bbox, SEARCH_TEXT + VARIANT dimensions / BOM / missing fields" },
  { name: "BOM_PARTS", type: "Table", purpose: "BOM master data keyed on PART_NUMBER" },
  { name: "V_BOM_RECONCILIATION", type: "View", purpose: "LEFT JOIN extractions to BOM; resolved values + source" },
  { name: "DRAWING_SEARCH", type: "Cortex Search Service", purpose: "Hybrid index on SEARCH_TEXT with 6 filter attributes" },
];

export default function Architecture() {
  return (
    <div className="bom-page arch-page">
      <h2>Architecture</h2>
      <p>
        Three tiers: a React SPA, a thin FastAPI layer, and Snowflake. Storage, extraction, embeddings,
        search and LLM inference all run inside Snowflake.
      </p>

      <div className="arch-stack">
        {LAYERS.map((layer, i) => (
          <div key={layer.key}>
            <div className={`arch-layer arch-${layer.key}`}>
              <div className="arch-layer-head">
                <span className="arch-layer-title">{layer.title}</span>
                <span className="arch-layer-sub">{layer.sub}</span>
              </div>
              <div className="arch-boxes">
                {layer.items.map((it) => (
                  <div key={it.name} className="arch-box">
                    <div className="arch-box-name">{it.name}</div>
                    <div className="arch-box-desc">{it.desc}</div>
                  </div>
                ))}
              </div>
              <div className="arch-layer-note">{layer.note}</div>
            </div>
            {i < LAYERS.length - 1 && (
              <div className="arch-connector">
                <span>{i === 0 ? "HTTP / JSON" : "Snowpark session · SQL + file PUT/GET"}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      <h3 className="arch-heading">Core Flows</h3>
      <div className="arch-flows">
        {FLOWS.map((f) => (
          <div key={f.title} className="ext-section arch-flow">
            <div className="arch-flow-head">
              <span className="arch-flow-title">{f.title}</span>
              <span className="meta-tag meta-material">{f.tag}</span>
            </div>
            <ol>
              {f.steps.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ol>
          </div>
        ))}
      </div>

      <h3 className="arch-heading">AI Functions</h3>
      <table className="bom-table">
        <thead>
          <tr>
            <th>Capability</th>
            <th>Function</th>
            <th>Model</th>
            <th>Where</th>
          </tr>
        </thead>
        <tbody>
          {AI_FUNCTIONS.map((r) => (
            <tr key={r.cap}>
              <td style={{ fontWeight: 600 }}>{r.cap}</td>
              <td style={{ fontFamily: "monospace" }}>{r.fn}</td>
              <td>{r.model}</td>
              <td style={{ color: "var(--text-muted)" }}>{r.where}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3 className="arch-heading">Snowflake Objects</h3>
      <table className="bom-table">
        <thead>
          <tr>
            <th>Object</th>
            <th>Type</th>
            <th>Purpose</th>
          </tr>
        </thead>
        <tbody>
          {OBJECTS.map((o) => (
            <tr key={o.name}>
              <td style={{ fontFamily: "monospace", color: "var(--navy)" }}>{o.name}</td>
              <td>{o.type}</td>
              <td style={{ color: "var(--text-secondary)" }}>{o.purpose}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
