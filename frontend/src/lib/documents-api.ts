/** Typed client for document verification (incl. multipart upload). */
import { apiFetch, ApiError } from "@/lib/api";
import { apiBaseUrl } from "@/lib/brand";

export interface Finding {
  field: string;
  code: string;
  severity: "error" | "warning" | "info";
  message: string;
  suggestion: string;
}
export interface ExtractedFieldOut {
  field_name: string;
  raw_value: string;
  normalized_value: string;
  issue: string;
  suggestion: string;
  confidence: number;
}
export interface AnalysisOut {
  id: string;
  engine: string;
  status: string;
  overall_confidence: number;
  summary: string;
  findings: Finding[];
  compliance: Record<string, unknown>;
  fields: ExtractedFieldOut[];
  created_at: string;
}
export interface DocumentOut {
  id: string;
  doc_type: string;
  status: string;
  display_name: string;
  retention_until: string;
  created_at: string;
}
export interface DocumentDetail extends DocumentOut {
  analyses: AnalysisOut[];
}

async function uploadDocument(
  token: string,
  file: File,
  docType: string,
  consent: boolean,
): Promise<DocumentDetail> {
  const form = new FormData();
  form.append("file", file);
  form.append("doc_type", docType);
  form.append("consent", String(consent));

  let resp: Response;
  try {
    resp = await fetch(`${apiBaseUrl}/documents`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` }, // no Content-Type: browser sets the boundary
      body: form,
    });
  } catch {
    throw new ApiError("Cannot reach the server.", "network_error", 0);
  }
  const text = await resp.text();
  const data = text ? JSON.parse(text) : null;
  if (!resp.ok) {
    const env = data as { error?: { message?: string; code?: string } } | null;
    throw new ApiError(env?.error?.message ?? "Upload failed.", env?.error?.code ?? "error", resp.status);
  }
  return data as DocumentDetail;
}

export const documentsApi = {
  upload: uploadDocument,
  list: (token: string) => apiFetch<DocumentOut[]>("/documents", { token }),
  get: (token: string, id: string) => apiFetch<DocumentDetail>(`/documents/${id}`, { token }),
  remove: (token: string, id: string) =>
    apiFetch<null>(`/documents/${id}`, { method: "DELETE", token }),
};
