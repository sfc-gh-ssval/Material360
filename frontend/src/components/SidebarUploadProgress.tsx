import { useSyncExternalStore } from "react";
import { uploadStore } from "../stores/uploadStore";
import type { UploadJob } from "../stores/uploadStore";

function useUploadJobs(): UploadJob[] {
  return useSyncExternalStore(
    (cb) => uploadStore.subscribe(cb),
    () => uploadStore.getJobs()
  );
}

export default function SidebarUploadProgress() {
  const jobs = useUploadJobs();
  const active = jobs.filter((j) => j.status === "uploading" || j.status === "extracting");
  const recent = jobs.filter((j) => j.status === "done" || j.status === "error");

  if (jobs.length === 0) return null;

  return (
    <div className="sidebar-uploads">
      {active.length > 0 && (
        <div className="sidebar-upload-section">
          <div className="sidebar-upload-label">Processing</div>
          {active.map((j) => (
            <div key={j.id} className="sidebar-upload-job">
              <div className="sidebar-upload-name" title={j.name}>{j.name}</div>
              <div className="sidebar-upload-bar">
                <div
                  className="sidebar-upload-fill active"
                  style={{ width: `${j.progress}%` }}
                />
              </div>
              <div className="sidebar-upload-status">
                {j.status === "uploading" ? "Uploading..." : "Extracting..."}
              </div>
            </div>
          ))}
        </div>
      )}
      {recent.length > 0 && (
        <div className="sidebar-upload-section">
          <div className="sidebar-upload-label">
            Recent
            <button
              className="sidebar-upload-dismiss"
              onClick={() => uploadStore.clearDone()}
            >
              Clear
            </button>
          </div>
          {recent.map((j) => (
            <div key={j.id} className="sidebar-upload-job">
              <div className="sidebar-upload-name" title={j.name}>{j.name}</div>
              <div className="sidebar-upload-bar">
                <div
                  className={`sidebar-upload-fill ${j.status === "done" ? "done" : "error"}`}
                  style={{ width: j.status === "done" ? "100%" : "100%" }}
                />
              </div>
              <div className={`sidebar-upload-status ${j.status}`}>
                {j.status === "done" ? "Complete" : "Failed"}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
