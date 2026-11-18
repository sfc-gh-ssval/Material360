import { useState, useEffect } from "react";
import { fetchReconciliation, type Reconciliation } from "../services/api";

export default function ReconciliationPage() {
  const [rows, setRows] = useState<Reconciliation[]>([]);

  useEffect(() => {
    fetchReconciliation().then(setRows);
  }, []);

  return (
    <div className="bom-page">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h2>BOM Reconciliation</h2>
          <p>
            Cross-references drawing extractions with BOM data. Highlights where missing drawing fields
            were filled from the BOM.
          </p>
        </div>
        <span style={{ fontSize: 13, color: "var(--text-muted)", whiteSpace: "nowrap", marginTop: 2 }}>
          {rows.length} {rows.length === 1 ? "row" : "rows"}
        </span>
      </div>

      <table className="bom-table">
        <thead>
          <tr>
            <th>Part Number</th>
            <th>Part Name</th>
            <th>Language</th>
            <th>Drawing Material</th>
            <th>BOM Material</th>
            <th>Resolved</th>
            <th>Source</th>
            <th>Drawing Finish</th>
            <th>BOM Finish</th>
            <th>Resolved Finish</th>
            <th>Finish Source</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td style={{ fontFamily: "monospace" }}>{r.PART_NUMBER}</td>
              <td>{r.PART_NAME}</td>
              <td>{r.SOURCE_LANGUAGE_NAME}</td>
              <td>
                {r.DRAWING_MATERIAL ? (
                  <span style={{ color: "var(--green)" }}>{r.DRAWING_MATERIAL}</span>
                ) : (
                  <span className="source-badge source-none">missing</span>
                )}
              </td>
              <td>{r.BOM_MATERIAL || "--"}</td>
              <td style={{ fontWeight: 600, color: r.MATERIAL_SOURCE === "MISSING" ? "var(--red)" : undefined }}>
                {r.RECONCILED_MATERIAL || "MISSING"}
              </td>
              <td>
                <SourceBadge source={r.MATERIAL_SOURCE} />
              </td>
              <td>
                {r.DRAWING_FINISH ? (
                  <span style={{ color: "var(--green)" }}>{r.DRAWING_FINISH}</span>
                ) : (
                  <span className="source-badge source-none">missing</span>
                )}
              </td>
              <td>{r.BOM_FINISH || "--"}</td>
              <td style={{ fontWeight: 600, color: r.FINISH_SOURCE === "MISSING" ? "var(--red)" : undefined }}>
                {r.RECONCILED_FINISH || "MISSING"}
              </td>
              <td>
                <SourceBadge source={r.FINISH_SOURCE} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="legend">
        <div className="legend-item">
          <div className="legend-dot" style={{ background: "var(--green)" }} /> From drawing
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ background: "var(--yellow)" }} /> Filled from BOM
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ background: "var(--red)" }} /> Missing from both
        </div>
      </div>
    </div>
  );
}

function SourceBadge({ source }: { source: string }) {
  if (source === "From drawing") return <span className="source-badge source-dwg">Drawing</span>;
  if (source === "Filled from BOM") return <span className="source-badge source-bom">BOM</span>;
  return <span className="source-badge source-none">--</span>;
}
