export interface UploadJob {
  id: string;
  name: string;
  status: "uploading" | "extracting" | "done" | "error";
  progress: number;
  result?: string;
  error?: string;
  language?: string;
}

type Listener = () => void;

let jobs: UploadJob[] = [];
let doneCount = 0;
const listeners = new Set<Listener>();
const doneListeners = new Set<Listener>();

function notify() {
  listeners.forEach((fn) => fn());
}

function notifyDone() {
  doneListeners.forEach((fn) => fn());
}

export const uploadStore = {
  getJobs: () => jobs,
  getDoneCount: () => doneCount,

  subscribe(fn: Listener) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  },

  subscribeDone(fn: Listener) {
    doneListeners.add(fn);
    return () => doneListeners.delete(fn);
  },

  addJob(job: UploadJob) {
    jobs = [job, ...jobs];
    notify();
  },

  updateJob(id: string, patch: Partial<UploadJob>) {
    const wasDone = jobs.find((j) => j.id === id)?.status === "done";
    jobs = jobs.map((j) => (j.id === id ? { ...j, ...patch } : j));
    notify();
    if (!wasDone && patch.status === "done") {
      doneCount++;
      notifyDone();
    }
  },

  dismissJob(id: string) {
    jobs = jobs.filter((j) => j.id !== id);
    notify();
  },

  clearDone() {
    jobs = jobs.filter((j) => j.status !== "done" && j.status !== "error");
    notify();
  },
};
