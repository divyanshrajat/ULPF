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
      'X-ULPF-User': 'admin',
      'X-ULPF-Role': 'administrator',
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

// ─── Onboarding ──────────────────────────────────────────────────────────────

export const createOnboardingSession = (sourceId: string) =>
  apiFetch<any>('/onboarding', {
    method: 'POST',
    body: JSON.stringify({ source_id: sourceId }),
  });

export const uploadSamples = (sessionId: string, samples: string[]) =>
  apiFetch<any>(`/onboarding/${sessionId}/samples`, {
    method: 'POST',
    body: JSON.stringify(samples),
  });

export const generateDraftRule = (sessionId: string, samples: string[]) =>
  apiFetch<any>(`/onboarding/${sessionId}/draft`, {
    method: 'POST',
    body: JSON.stringify(samples),
  });

export const validateRule = (sessionId: string, ruleVersionId: string, samples: string[]) =>
  apiFetch<any>(`/onboarding/${sessionId}/validate`, {
    method: 'POST',
    body: JSON.stringify({ rule_version_id: ruleVersionId, samples }),
  });

// We keep the old onboarding approve for compatibility, but the new preferred way is via Rules
export const approveRule = (sessionId: string, ruleVersionId: string) =>
  apiFetch<any>(`/onboarding/${sessionId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ rule_version_id: ruleVersionId }),
  });

export const analyzeLog = async (data: { source_id: string, raw_payload: any, target_schema: string }) => {
  const session = await createOnboardingSession(data.source_id);
  const rawStr = typeof data.raw_payload === 'string' ? data.raw_payload : JSON.stringify(data.raw_payload);
  const sampleRes = await uploadSamples(session.session_id, [rawStr]);
  
  if (sampleRes.active_rule_found) {
    const ruleDetails = await fetchRule(sampleRes.active_rule_id);
    const versions = ruleDetails.versions || [];
    const activeVersion = versions.find((v: any) => v.status === 'ACTIVE') || versions[0];
    if (activeVersion) {
      const validateRes = await validateRule(session.session_id, activeVersion.id, [rawStr]);
      return {
        status: 'matched_existing',
        rule_id: sampleRes.active_rule_id,
        rule_json: { field_mappings: activeVersion.field_mappings },
        normalized_payload: validateRes.results[0]?.normalized_payload || validateRes.results[0]?.extracted || {},
        error: !validateRes.passed || validateRes.results[0]?.error ? validateRes.results[0]?.error || "Validation failed" : null
      };
    }
  }
  
  const draftRes = await generateDraftRule(session.session_id, [rawStr]);
  const validateRes = await validateRule(session.session_id, draftRes.version, [rawStr]);
  
  return {
    status: 'drafted',
    rule_id: draftRes.rule_id,
    version: draftRes.version,
    session_id: session.session_id,
    llm_mode: draftRes.llm_mode,
    rule_json: draftRes.rule_json,
    normalized_payload: validateRes.results[0]?.normalized_payload || validateRes.results[0]?.extracted || {},
    error: !validateRes.passed || validateRes.results[0]?.error ? validateRes.results[0]?.error || "Validation failed" : null
  };
};

// ─── Rules ───────────────────────────────────────────────────────────────────

export const fetchRules = () => apiFetch<any[]>('/rules');
export const fetchRule = (ruleId: string) => apiFetch<any>(`/rules/${ruleId}`);

export const approveRuleVersion = (ruleId: string, versionId: string) =>
  apiFetch<any>(`/rules/${ruleId}/versions/${versionId}/approve`, { method: 'POST' });

export const rejectRuleVersion = (ruleId: string, versionId: string) =>
  apiFetch<any>(`/rules/${ruleId}/versions/${versionId}/reject`, { method: 'POST' });

export const updateRuleLifecycle = (ruleId: string, payload: { action: string }) => 
  apiFetch<any>(`/rules/${ruleId}/lifecycle`, { method: 'POST', body: JSON.stringify(payload) });

// ─── Events ───────────────────────────────────────────────────────────────────

export const fetchEvents = (params?: {
  source_id?: string;
  rule_id?: string;
  processing_path?: string;
  page?: number;
  page_size?: number;
}) => {
  const qs = new URLSearchParams();
  if (params?.source_id) qs.set('source_id', params.source_id);
  if (params?.rule_id) qs.set('rule_id', params.rule_id);
  if (params?.processing_path) qs.set('processing_path', params.processing_path);
  if (params?.page) qs.set('page', String(params.page));
  if (params?.page_size) qs.set('page_size', String(params.page_size));
  return apiFetch<any>(`/events?${qs}`);
};

export const fetchEvent = (eventId: string) => apiFetch<any>(`/events/${eventId}`);
export const fetchEventRaw = (eventId: string) => apiFetch<any>(`/events/${eventId}/raw`);
export const fetchEventTrace = (eventId: string) => apiFetch<any>(`/events/${eventId}/trace`);

export const getExportUrl = (format: string, sourceId?: string) => {
  const qs = new URLSearchParams({ format });
  if (sourceId) qs.set('source_id', sourceId);
  return `${API_BASE}/events/export?${qs}`;
};

// ─── Jobs & Sessions ─────────────────────────────────────────────────────────

export const fetchJobs = (params?: { source_id?: string; page?: number; page_size?: number }) => {
  const qs = new URLSearchParams();
  if (params?.source_id) qs.set('source_id', params.source_id);
  if (params?.page) qs.set('page', String(params.page));
  if (params?.page_size) qs.set('page_size', String(params.page_size));
  return apiFetch<any>(`/jobs?${qs}`);
};

export const fetchJob = (jobId: string) => apiFetch<any>(`/jobs/${jobId}`);

// For file uploads, we use native fetch with FormData so we don't JSON.stringify the body
export const createJob = async (sourceId: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/jobs?source_id=${sourceId}`, {
    method: 'POST',
    headers: {
      'X-ULPF-User': 'admin',
      'X-ULPF-Role': 'administrator',
    },
    body: formData,
  });
  if (!res.ok) throw await res.json();
  return res.json();
};

export const fetchSessions = (params?: { source_id?: string; page?: number; page_size?: number }) => {
  const qs = new URLSearchParams();
  if (params?.source_id) qs.set('source_id', params.source_id);
  if (params?.page) qs.set('page', String(params.page));
  if (params?.page_size) qs.set('page_size', String(params.page_size));
  return apiFetch<any>(`/sessions?${qs}`);
};

export const fetchSession = (sessionId: string) => apiFetch<any>(`/sessions/${sessionId}`);

export const createSession = (sourceId: string) =>
  apiFetch<any>('/sessions', {
    method: 'POST',
    body: JSON.stringify({ source_id: sourceId })
  });

export const submitSessionEvents = (sessionId: string, events: string[]) =>
  apiFetch<any>(`/sessions/${sessionId}/events`, {
    method: 'POST',
    body: JSON.stringify(events)
  });

// ─── API Keys ────────────────────────────────────────────────────────────────

export const fetchApiKeys = () => apiFetch<any[]>('/api-keys');

export const createApiKey = (data: { name: string; source_scope?: string; environment?: string }) =>
  apiFetch<any>('/api-keys', { method: 'POST', body: JSON.stringify(data) });

export const revokeApiKey = (keyId: string) =>
  apiFetch<any>(`/api-keys/${keyId}`, { method: 'DELETE' });

// ─── System & Misc ───────────────────────────────────────────────────────────

export const fetchStats = () => apiFetch<any>('/stats/overview');
export const fetchHealth = () => apiFetch<any>('/system/health');


