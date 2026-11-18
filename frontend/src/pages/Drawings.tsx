import { useState, useEffect, useSyncExternalStore } from "react";
import { fetchExtractions, getFilePreviewUrl, type Extraction } from "../services/api";
import { uploadStore } from "../stores/uploadStore";

const TOTAL_FIELDS = 10;

function fieldCount(e: Extraction): number {
  const missing = Array.isArray(e.MISSING_FIELDS) ? e.MISSING_FIELDS.length : 0;
  return TOTAL_FIELDS - missing;
}

function statusClass(e: Extraction): string {
  const count = fieldCount(e);
  if (count >= TOTAL_FIELDS) return "complete";
  if (count >= 7) return "partial";
  return "low";
}

function statusWidth(e: Extraction): string {
  return `${(fieldCount(e) / TOTAL_FIELDS) * 100}%`;
}

export default function Drawings() {
  const [extractions, setExtractions] = useState<Extraction[]>([]);
  const [selected, setSelected] = useState<Extraction | null>(null);
  const [tab, setTab] = useState<"doc" | "extraction" | "bom" | "json">("extraction");
  const [search, setSearch] = useState("");

  const doneCount = useSyncExternalStore(
    (cb) => uploadStore.subscribeDone(cb),
    () => uploadStore.getDoneCount()
  );

  useEffect(() => {
    fetchExtractions().then(setExtractions);
  }, [doneCount]);

  const filtered = extractions.filter(
    (e) =>
      !search ||
      (e.PART_NUMBER || "").toLowerCase().includes(search.toLowerCase()) ||
      (e.PART_NAME || "").toLowerCase().includes(search.toLowerCase()) ||
      (e.MATERIAL || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="drawings-page">
      <div className="drawings-list">
        <div className="list-header">
          <h2>Drawings <span className="drawings-count">{extractions.length}</span></h2>
          <input
            className="search-box"
            placeholder="Search by part number, name, material..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="list-items">
          {filtered.map((e) => (
            <div
              key={e.EXTRACTION_ID}
              className={`drawing-card ${selected?.EXTRACTION_ID === e.EXTRACTION_ID ? "selected" : ""}`}
              onClick={() => { setSelected(e); setTab("extraction"); }}
            >
              <div className="card-top">
                <span className="card-part-num">{e.PART_NUMBER}</span>
                <span className="card-rev">Rev {e.REVISION}</span>
              </div>
              <div className="card-name">{e.PART_NAME}</div>
              <div className="card-meta">
                {e.MATERIAL && <span className="meta-tag meta-material">{e.MATERIAL}</span>}
                {e.FINISH && <span className="meta-tag meta-finish">{e.FINISH}</span>}
                {e.WAS_TRANSLATED ? (
                  <span className="meta-tag meta-lang">
                    {e.SOURCE_LANGUAGE?.toUpperCase()} &rarr; EN
                  </span>
                ) : (
                  <span className="meta-tag meta-lang-en">EN</span>
                )}
              </div>
              <div className="card-status">
                <div className="status-bar">
                  <div className={`status-fill ${statusClass(e)}`} style={{ width: statusWidth(e) }} />
                </div>
                <span className="status-text">
                  {fieldCount(e)}/{TOTAL_FIELDS}
                  {Array.isArray(e.MISSING_FIELDS) && e.MISSING_FIELDS.length > 0
                    ? ` \u00b7 ${e.MISSING_FIELDS.length} missing`
                    : " fields"}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="drawings-detail">
        {!selected ? (
          <div className="empty-state">Select a drawing to view details</div>
        ) : (
          <>
            <div className="detail-header">
              <span className="detail-filename">{selected.FILE_NAME}</span>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                {selected.EXTRACTION_TIMESTAMP}
              </span>
            </div>
            <div className="detail-tabs">
              {(["doc", "extraction", "bom", "json"] as const).map((t) => (
                <button
                  key={t}
                  className={`detail-tab ${tab === t ? "active" : ""}`}
                  onClick={() => setTab(t)}
                >
                  {t === "doc" ? "Document" : t === "extraction" ? "Extraction" : t === "bom" ? "BOM" : "Raw JSON"}
                </button>
              ))}
            </div>
            <div className="detail-body">
              {tab === "doc" && (
                <iframe
                  className="pdf-viewer"
                  src={getFilePreviewUrl(selected.FILE_NAME)}
                  title="Drawing Preview"
                  style={{ width: "100%", height: "100%", minHeight: 600 }}
                />
              )}
              {tab === "extraction" && <ExtractionView e={selected} />}
              {tab === "bom" && <BomView e={selected} />}
              {tab === "json" && (
                <pre className="json-pre">
                  {JSON.stringify(
                    {
                      part_number: selected.PART_NUMBER,
                      part_name: selected.PART_NAME,
                      original_part_name: selected.ORIGINAL_PART_NAME,
                      revision: selected.REVISION,
                      material: selected.MATERIAL,
                      finish: selected.FINISH,
                      original_finish: selected.ORIGINAL_FINISH,
                      source_language: selected.SOURCE_LANGUAGE,
                      source_language_name: selected.SOURCE_LANGUAGE_NAME,
                      was_translated: selected.WAS_TRANSLATED,
                      weight_kg: selected.WEIGHT_KG,
                      cosmetic_requirement: selected.COSMETIC_REQUIREMENT,
                      designer: selected.DESIGNER,
                      draftsman: selected.DRAFTSMAN,
                      bounding_box: { x: selected.BBOX_X, y: selected.BBOX_Y, z: selected.BBOX_Z, source: selected.BBOX_SOURCE },
                      missing_fields: selected.MISSING_FIELDS,
                      critical_dimensions: selected.CRITICAL_DIMENSIONS,
                      bom: selected.BOM,
                    },
                    null,
                    2
                  )}
                </pre>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ExtractionView({ e }: { e: Extraction }) {
  return (
    <div className="extraction-grid">
      <div className="ext-section">
        <h3>Title Block</h3>
        <div className="ext-field"><span className="ext-label">Part Number</span><span className="ext-value" style={{ fontFamily: "monospace" }}>{e.PART_NUMBER}</span></div>
        <div className="ext-field"><span className="ext-label">Part Name</span><span className={`ext-value ${e.WAS_TRANSLATED ? "translated" : ""}`}>{e.PART_NAME || <span className="ext-value missing">--</span>}</span></div>
        <div className="ext-field"><span className="ext-label">Revision</span><span className="ext-value">{e.REVISION}</span></div>
        <div className="ext-field"><span className="ext-label">Material</span><span className={`ext-value ${!e.MATERIAL ? "missing" : ""}`}>{e.MATERIAL || "Missing"}</span></div>
        <div className="ext-field"><span className="ext-label">Finish</span><span className={`ext-value ${!e.FINISH ? "missing" : ""} ${e.WAS_TRANSLATED && e.FINISH ? "translated" : ""}`}>{e.FINISH || "Missing"}</span></div>
        <div className="ext-field"><span className="ext-label">Cosmetic</span><span className={`ext-value ${!e.COSMETIC_REQUIREMENT ? "missing" : ""}`}>{e.COSMETIC_REQUIREMENT || "None specified"}</span></div>
        <div className="ext-field"><span className="ext-label">Weight</span><span className="ext-value">{e.WEIGHT_KG ? `${e.WEIGHT_KG} kg` : "--"}</span></div>
        <div className="ext-field"><span className="ext-label">Designer</span><span className={`ext-value ${!e.DESIGNER ? "missing" : ""}`}>{e.DESIGNER || "--"}</span></div>
        <div className="ext-field"><span className="ext-label">Draftsman</span><span className={`ext-value ${!e.DRAFTSMAN ? "missing" : ""}`}>{e.DRAFTSMAN || "--"}</span></div>
      </div>

      <div className="ext-section">
        <h3>Language</h3>
        <div className="ext-field"><span className="ext-label">Detected</span><span className="ext-value" style={{ color: e.WAS_TRANSLATED ? "var(--yellow)" : "var(--green)" }}>{e.SOURCE_LANGUAGE_NAME} ({e.SOURCE_LANGUAGE?.toUpperCase()})</span></div>
        <div className="ext-field"><span className="ext-label">Translated</span><span className="ext-value" style={{ color: e.WAS_TRANSLATED ? "var(--green)" : "var(--text-muted)" }}>{e.WAS_TRANSLATED ? "Yes" : "No"}</span></div>
        {e.ORIGINAL_PART_NAME && e.WAS_TRANSLATED && (
          <div className="original-block">
            <div className="original-label">Original Part Name</div>
            <div className="original-text">{e.ORIGINAL_PART_NAME}</div>
          </div>
        )}
        {e.ORIGINAL_FINISH && e.WAS_TRANSLATED && (
          <div className="original-block">
            <div className="original-label">Original Finish</div>
            <div className="original-text">{e.ORIGINAL_FINISH}</div>
          </div>
        )}
        <h3 style={{ marginTop: 16 }}>Bounding Box</h3>
        <div className="ext-field"><span className="ext-label">X</span><span className="ext-value">{e.BBOX_X ? `${e.BBOX_X} mm` : "--"}</span></div>
        <div className="ext-field"><span className="ext-label">Y</span><span className="ext-value">{e.BBOX_Y ? `${e.BBOX_Y} mm` : "--"}</span></div>
        <div className="ext-field"><span className="ext-label">Z</span><span className="ext-value">{e.BBOX_Z ? `${e.BBOX_Z} mm` : "--"}</span></div>
        {e.BBOX_SOURCE && <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>Source: {e.BBOX_SOURCE}</div>}
      </div>

      <div className="ext-section full-width">
        <h3>Missing Fields</h3>
        {Array.isArray(e.MISSING_FIELDS) && e.MISSING_FIELDS.length > 0 ? (
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {e.MISSING_FIELDS.map((f) => <span key={f} className="missing-badge">{f}</span>)}
          </div>
        ) : (
          <div style={{ fontSize: 12, color: "var(--green)" }}>All fields extracted successfully</div>
        )}
      </div>

      <div className="ext-section full-width">
        <h3>Critical Dimensions</h3>
        {Array.isArray(e.CRITICAL_DIMENSIONS) && e.CRITICAL_DIMENSIONS.length > 0 ? (
          <table className="ext-table">
            <thead><tr><th>Value</th><th>Tolerance</th><th>Location</th><th>Source Evidence</th></tr></thead>
            <tbody>
              {e.CRITICAL_DIMENSIONS.map((d, i) => (
                <tr key={i}>
                  <td>{d.value}</td>
                  <td style={{ color: d.tolerance ? "var(--yellow)" : "var(--text-muted)" }}>{d.tolerance || "--"}</td>
                  <td>{d.location_on_drawing}</td>
                  <td style={{ fontFamily: "monospace", fontSize: 11, color: "var(--text-muted)" }}>{d.source_evidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>No dimensions extracted</div>
        )}
      </div>
    </div>
  );
}

function BomView({ e }: { e: Extraction }) {
  const bom = Array.isArray(e.BOM) ? e.BOM : [];
  if (bom.length === 0) {
    return <div className="empty-state">No BOM on this drawing</div>;
  }
  return (
    <div className="ext-section full-width" style={{ background: "transparent", border: "none", padding: 0 }}>
      <h3>Drawing BOM {e.WAS_TRANSLATED ? "(Translated)" : ""}</h3>
      <table className="ext-table" style={{ marginTop: 8 }}>
        <thead>
          <tr>
            <th>Pos</th>
            <th>Description (EN)</th>
            {e.WAS_TRANSLATED && <th>Original</th>}
            <th>Material</th>
            <th>Qty</th>
          </tr>
        </thead>
        <tbody>
          {bom.map((item, i) => (
            <tr key={i}>
              <td>{item.pos}</td>
              <td>{item.description}</td>
              {e.WAS_TRANSLATED && <td style={{ color: "var(--yellow)" }}>{item.original_description}</td>}
              <td>{item.material}</td>
              <td>{item.qty}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
