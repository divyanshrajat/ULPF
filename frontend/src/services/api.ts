/**
 * api.ts — Centralized API client for ULPF frontend.
 *
 * Uses relative /api/v1 base URL so the frontend works at:
 *   http://localhost:8000   (production/demo — served by FastAPI)
 *   http://localhost:5173   (Vite dev server with proxy to :8000)
 *
 * Never uses hardcoded absolute URLs in production builds.
 */

// Relative base — works in both single-origin (FastAPI) and Vite dev proxy modes.
export const API_BASE = '/api/v1';

// ─── Error handling ──────────────────────────────────────────────────────────

export interface ApiError {
  code: string;
  message: string;
  stage?: string;
  trace_id?: string | null;
  details?: Record<string, unknown>;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    let error: ApiError;
    try {
      const body = await res.json();
      error = body.detail ?? body;
    } catch {
      error = { code: 'HTTP_ERROR', message: `HTTP ${res.status}`, stage: path };
    }
    throw error;
  }

  return res.json();
}

// ─── Sources ─────────────────────────────────────────────────────────────────

export const fetchSources = () => apiFetch<any[]>('/sources');

export const fetchSource = (sourceId: string) => apiFetch<any>(`/sources/${sourceId}`);

export const createSource = (data: {
  name: string;
  vendor?: string;
  product?: string;
  transport?: string;
  format_hint?: string;
  namespace?: string;
}) => apiFetch<any>('/sources', { method: 'POST', body: JSON.stringify(data) });

export const updateSource = (sourceId: string, data: Record<string, any>) =>
  apiFetch<any>(`/sources/${sourceId}`, { method: 'PATCH', body: JSON.stringify(data) });

export const archiveSource = (sourceId: string) =>
  apiFetch<any>(`/sources/${sourceId}`, { method: 'DELETE' });

export const fetchSourceFiles = (sourceId: string) =>
  apiFetch<any[]>(`/sources/${sourceId}/files`);

export const fetchSourceTemplates = (sourceId: string) =>
  apiFetch<any[]>(`/sources/${sourceId}/templates`);

export const fetchSourceMappings = (sourceId: string) =>
  apiFetch<any[]>(`/sources/${sourceId}/mappings`);

export const fetchSourceEvents = (sourceId: string, page = 1) =>
  apiFetch<any>(`/sources/${sourceId}/events?page=${page}`);

export const fetchSourceDrift = (sourceId: string) =>
  apiFetch<any[]>(`/sources/${sourceId}/drift`);

// ─── Files ────────────────────────────────────────────────────────────────────

export const fetchFiles = (sourceId?: string) =>
  apiFetch<any[]>(`/files${sourceId ? `?source_id=${sourceId}` : ''}`);

export const fetchFile = (fileId: string) => apiFetch<any>(`/files/${fileId}`);

export const fetchFileStatus = (fileId: string) => apiFetch<any>(`/files/${fileId}/status`);

export const uploadFile = async (file: File, sourceId: string): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source_id', sourceId);

  const res = await fetch(`${API_BASE}/files/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw body.detail ?? { code: 'UPLOAD_FAILED', message: `Upload failed: HTTP ${res.status}` };
  }
  return res.json();
};

// ─── Onboarding ──────────────────────────────────────────────────────────────

export const fetchOnboardingSessions = (sourceId?: string) =>
  apiFetch<any[]>(`/onboarding${sourceId ? `?source_id=${sourceId}` : ''}`);

export const fetchOnboardingSession = (id: string) => apiFetch<any>(`/onboarding/${id}`);

export const createOnboardingSession = (sourceId: string, fileId?: string) =>
  apiFetch<any>('/onboarding', {
    method: 'POST',
    body: JSON.stringify({ source_id: sourceId, file_id: fileId }),
  });

export const uploadOnboardingFile = async (
  sessionId: string,
  file: File
): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/onboarding/${sessionId}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw body.detail ?? { code: 'UPLOAD_FAILED', message: `Upload failed: HTTP ${res.status}` };
  }
  return res.json();
};

export const processOnboardingSession = (sessionId: string) =>
  apiFetch<any>(`/onboarding/${sessionId}/process`, { method: 'POST', body: '{}' });

// ─── Reviews ─────────────────────────────────────────────────────────────────

export const fetchReviews = (params?: { source_id?: string; status?: string; page?: number }) => {
  const qs = new URLSearchParams();
  if (params?.source_id) qs.set('source_id', params.source_id);
  if (params?.status) qs.set('status', params.status);
  if (params?.page) qs.set('page', String(params.page));
  return apiFetch<any>(`/reviews?${qs}`);
};

export const fetchReview = (reviewId: string) => apiFetch<any>(`/reviews/${reviewId}`);

export const approveReview = (reviewId: string, fieldBindings: Record<string, string>) =>
  apiFetch<any>(`/reviews/${reviewId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ field_bindings: fieldBindings }),
  });

export const reassignReview = (
  reviewId: string,
  sourceField: string,
  oldTarget: string,
  newTarget: string,
  reason: string
) =>
  apiFetch<any>(`/reviews/${reviewId}/reassign`, {
    method: 'POST',
    body: JSON.stringify({ source_field: sourceField, old_target: oldTarget, new_target: newTarget, reason }),
  });

export const markExtensionOnly = (reviewId: string, sourceField: string) =>
  apiFetch<any>(`/reviews/${reviewId}/extension`, {
    method: 'POST',
    body: JSON.stringify({ source_field: sourceField }),
  });

export const rejectReview = (reviewId: string) =>
  apiFetch<any>(`/reviews/${reviewId}/reject`, { method: 'POST', body: '{}' });

// ─── Traces ───────────────────────────────────────────────────────────────────

export const fetchTraces = (params?: { source_id?: string; page?: number }) => {
  const qs = new URLSearchParams();
  if (params?.source_id) qs.set('source_id', params.source_id);
  if (params?.page) qs.set('page', String(params.page));
  return apiFetch<any>(`/traces?${qs}`);
};

export const fetchTrace = (traceId: string) => apiFetch<any>(`/traces/${traceId}`);

export const fetchTraceTimeline = (traceId: string) =>
  apiFetch<any>(`/traces/${traceId}/timeline`);

export const fetchTraceRaw = (traceId: string) => apiFetch<any>(`/traces/${traceId}/raw`);

export const fetchTraceNormalized = (traceId: string) =>
  apiFetch<any>(`/traces/${traceId}/normalized`);

export const fetchTraceProvenance = (traceId: string) =>
  apiFetch<any[]>(`/traces/${traceId}/provenance`);

export const fetchTraceIntegrity = (traceId: string) =>
  apiFetch<any>(`/traces/${traceId}/integrity`);

// ─── Events ───────────────────────────────────────────────────────────────────

export const fetchEvents = (params?: {
  source_id?: string;
  processing_path?: string;
  page?: number;
  page_size?: number;
}) => {
  const qs = new URLSearchParams();
  if (params?.source_id) qs.set('source_id', params.source_id);
  if (params?.processing_path) qs.set('processing_path', params.processing_path);
  if (params?.page) qs.set('page', String(params.page));
  if (params?.page_size) qs.set('page_size', String(params.page_size));
  return apiFetch<any>(`/events?${qs}`);
};

// ─── Mappings ────────────────────────────────────────────────────────────────

export const fetchMappings = () => apiFetch<any[]>('/mappings');

// ─── Schemas ─────────────────────────────────────────────────────────────────

export const fetchSchemas = () => apiFetch<any[]>('/schemas');

export const fetchSchema = (version: string) => apiFetch<any>(`/schemas/${version}`);

// ─── Stats & Dashboard ───────────────────────────────────────────────────────

export const fetchStats = () => apiFetch<any>('/stats/overview');

// ─── Health ──────────────────────────────────────────────────────────────────

export const fetchHealth = () => apiFetch<any>('/system/health/details');

export const fetchAirgapStatus = () => apiFetch<any>('/system/airgap');

// ─── System Config ───────────────────────────────────────────────────────────

export const fetchSystemConfig = () => apiFetch<any>('/system/config');

// ─── Audit ───────────────────────────────────────────────────────────────────

export const fetchAuditLog = (page = 1) => apiFetch<any>(`/audit?page=${page}`);

// ─── Provenance ──────────────────────────────────────────────────────────────

export const searchProvenance = (params: {
  normalized_field?: string;
  source_field?: string;
}) => {
  const qs = new URLSearchParams(params as Record<string, string>);
  return apiFetch<any>(`/provenance/search?${qs}`);
};

// ─── Export ───────────────────────────────────────────────────────────────────

export const getExportUrl = (format: 'json' | 'ndjson' = 'ndjson', sourceId?: string) => {
  const base = `${API_BASE}/export/events`;
  if (format === 'ndjson') return sourceId ? `${base}.ndjson?source_id=${sourceId}` : `${base}.ndjson`;
  return sourceId ? `${base}?source_id=${sourceId}` : base;
};

// ─── Queue (legacy) ──────────────────────────────────────────────────────────

export const fetchQueue = () =>
  fetchReviews({ status: 'PENDING' }).then((r) => r.items ?? []);
