import { useState, useRef, useCallback } from "react";
import { useSyncExternalStore } from "react";
import { uploadFile } from "../services/api";
import { uploadStore } from "../stores/uploadStore";
import type { UploadJob } from "../stores/uploadStore";

function useUploadJobs(): UploadJob[] {
  return useSyncExternalStore(
    (cb) => uploadStore.subscribe(cb),
    () => uploadStore.getJobs()
  );
}

let counter = 0;

export default function Upload() {
  const uploads = useUploadJobs();
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(async (files: FileList) => {
    for (const file of Array.from(files)) {
      const id = `upload-${++counter}-${Date.now()}`;
      uploadStore.addJob({ id, name: file.name, status: "uploading", progress: 30 });

      try {
        uploadStore.updateJob(id, { status: "extracting", progress: 60 });

        const res = await uploadFile(file);
        const ext = res.data.extraction;

        uploadStore.updateJob(id, {
          status: "done",
          progress: 100,
          result: `${ext.part_number || "?"} - ${ext.part_name || "extracted"}`,
          language: ext.source_language_name || "Unknown",
        });
      } catch (err: any) {
        uploadStore.updateJob(id, {
          status: "error",
          progress: 0,
          error: err.message || "Upload failed",
        });
      }
    }
  }, []);

  return (
    <div className="upload-page">
      <h2>Upload Engineering Drawings</h2>
      <p>Upload PDF, JPEG, PNG, or TIFF files. Each drawing will be analyzed and extracted automatically.</p>

      <div
        className={`drop-zone ${dragOver ? "drag-over" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
        onClick={() => inputRef.current?.click()}
      >
        <div style={{ fontSize: 40, opacity: 0.3, marginBottom: 12 }}>&#128194;</div>
        <div className="drop-text">Drag and drop files here</div>
        <div className="drop-sub">PDF, JPEG, PNG, TIFF up to 50 MB</div>
        <button className="drop-btn" onClick={(e) => e.stopPropagation()}>Browse Files</button>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.png,.jpg,.jpeg,.tiff,.tif"
          style={{ display: "none" }}
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
      </div>

      {uploads.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3 style={{ fontSize: 14, marginBottom: 12, color: "var(--text-muted)" }}>Recent Uploads</h3>
          {uploads.map((u) => (
            <div key={u.id} className="upload-item">
              <div className="upload-item-top">
                <span className="upload-item-name">{u.name}</span>
                <span className="upload-item-time">{u.status === "done" ? "Complete" : ""}</span>
              </div>
              <div className="upload-progress">
                <div
                  className={`upload-progress-fill ${u.status === "done" ? "done" : ""}`}
                  style={{ width: `${u.progress}%` }}
                />
              </div>
              <div className="upload-item-status">
                {u.status === "uploading" && <span style={{ color: "var(--accent)" }}>Uploading...</span>}
                {u.status === "extracting" && (
                  <span style={{ color: "var(--yellow)" }}>Extracting... detecting language, translating...</span>
                )}
                {u.status === "done" && (
                  <span style={{ color: "var(--green)" }}>
                    Complete -- {u.result} | Language: {u.language}
                  </span>
                )}
                {u.status === "error" && <span style={{ color: "var(--red)" }}>Error: {u.error}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
