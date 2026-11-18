import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

export interface Extraction {
  EXTRACTION_ID: string;
  FILE_NAME: string;
  PART_NUMBER: string;
  PART_NAME: string;
  ORIGINAL_PART_NAME: string;
  REVISION: string;
  MATERIAL: string;
  FINISH: string;
  ORIGINAL_FINISH: string;
  COSMETIC_REQUIREMENT: string;
  DESIGNER: string;
  DRAFTSMAN: string;
  SOURCE_LANGUAGE: string;
  SOURCE_LANGUAGE_NAME: string;
  WAS_TRANSLATED: boolean;
  WEIGHT_KG: number;
  BBOX_X: number;
  BBOX_Y: number;
  BBOX_Z: number;
  BBOX_SOURCE: string;
  MISSING_FIELDS: string[];
  CRITICAL_DIMENSIONS: {
    value: string;
    tolerance: string | null;
    location_on_drawing: string;
    source_evidence: string;
  }[];
  BOM: {
    pos: number;
    description: string;
    original_description: string;
    material: string;
    qty: number;
  }[];
  ORIGINAL_BOM: { pos: number; description: string; material: string; qty: number }[];
  EXTRACTION_TIMESTAMP: string;
}

export interface Reconciliation {
  PART_NUMBER: string;
  PART_NAME: string;
  SOURCE_LANGUAGE_NAME: string;
  DRAWING_MATERIAL: string;
  BOM_MATERIAL: string;
  RECONCILED_MATERIAL: string;
  MATERIAL_SOURCE: string;
  DRAWING_FINISH: string;
  BOM_FINISH: string;
  RECONCILED_FINISH: string;
  FINISH_SOURCE: string;
  FILE_NAME: string;
}

export const fetchExtractions = () =>
  api.get<{ extractions: Extraction[] }>("/extractions").then((r) => r.data.extractions);

export const fetchExtraction = (id: string) =>
  api.get<Extraction>(`/extractions/${id}`).then((r) => r.data);

export const fetchReconciliation = () =>
  api.get<{ reconciliation: Reconciliation[] }>("/reconciliation").then((r) => r.data.reconciliation);

export const uploadFile = (file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  return api.post("/upload", fd);
};

export const agentChat = (question: string) =>
  api.post<{ answer: string }>("/agent/chat", { question }).then((r) => r.data);

export const getFilePreviewUrl = (filename: string) =>
  `/api/files/${encodeURIComponent(filename)}/preview`;

export default api;
