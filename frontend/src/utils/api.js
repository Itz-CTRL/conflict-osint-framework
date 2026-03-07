// src/utils/api.js
const API_BASE = 'http://127.0.0.1:5000';

/**
 * Core fetch wrapper — normalises errors and returns parsed JSON.
 */
export async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  let json;
  try {
    json = await res.json();
  } catch {
    throw new Error(`HTTP ${res.status} — non-JSON response`);
  }

  if (!res.ok) {
    throw new Error(json?.error || json?.message || `HTTP ${res.status}`);
  }

  return json;
}

/**
 * Consistent API surface for all Flask backend endpoints.
 */
export const api = {
  // ── Health ────────────────────────────────────────────
  health: () => apiFetch('/api/health'),

  // ── Username Suggestions ──────────────────────────────
  /** GET /api/username_suggestions?q=<query> → { status, suggestions: [...] } */
  usernameSuggestions: (query) => {
    if (!query || query.length < 2) return Promise.resolve({ suggestions: [] });
    return apiFetch(`/api/username_suggestions?q=${encodeURIComponent(query)}`);
  },

  // ── Investigations ────────────────────────────────────
  /** GET /api/investigation/list → { status, data: [...], pagination } */
  listInvestigations: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/api/investigation/list${qs ? '?' + qs : ''}`);
  },

  /** POST /api/investigation/create → { status, case_id, data } */
  createInvestigation: (username, email = '', phone = '', filters = {}) =>
    apiFetch('/api/investigation/create', {
      method: 'POST',
      body: JSON.stringify({ username, email: email || undefined, phone: phone || undefined, filters: filters || {} }),
    }),

  /** POST /api/investigation/scan/:caseId/:scanType → { status, case_id, data, graph, risk_score } */
  startScan: (caseId, scanType = 'light') =>
    apiFetch(`/api/investigation/scan/${caseId}/${scanType}`, { method: 'POST' }),

  /** GET /api/investigation/status/:caseId → { status, case_id, data: { status, risk_score, ... } } */
  getStatus: (caseId) => apiFetch(`/api/investigation/status/${caseId}`),

  /** GET /api/investigation/result/:caseId → { status, case_id, data, graph, risk_score } */
  getResult: (caseId) => apiFetch(`/api/investigation/result/${caseId}`),

  /** DELETE /api/investigation/delete/:caseId */
  deleteInvestigation: (caseId) =>
    apiFetch(`/api/investigation/delete/${caseId}`, { method: 'DELETE' }),

  // ── Phone Intelligence ────────────────────────────────
  /** POST /api/phone/lookup → { status, data: { number, country, carrier, ... } } */
  phoneLookup: (phone, countryCode = null, scanType = 'light') =>
    apiFetch('/api/phone/lookup', {
      method: 'POST',
      body: JSON.stringify({ 
        phone_number: phone,
        country_code: countryCode,
        scan_type: scanType
      }),
    }),

  /** POST /api/phone/scan → simplified single-button GhostTR-style scan */
  phoneScan: (phone) =>
    apiFetch('/api/phone/scan', {
      method: 'POST',
      body: JSON.stringify({ phone_number: phone }),
    }),

  /** POST /api/phone/batch → { status, data: [...], summary } */
  phoneBatch: (phones) =>
    apiFetch('/api/phone/batch', {
      method: 'POST',
      body: JSON.stringify({ phones }),
    }),

  /** GET /api/phone/history → { status, data: [...], pagination } */
  phoneHistory: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/api/phone/history${qs ? '?' + qs : ''}`);
  },

  // ── Graph ─────────────────────────────────────────────
  /** GET /api/graph/:caseId → { status, graph: { nodes, edges } } */
  getGraph: (caseId) => apiFetch(`/api/graph/${caseId}`),

  /** GET /api/graph/:caseId/statistics */
  getGraphStats: (caseId) => apiFetch(`/api/graph/${caseId}/statistics`),

  /** GET /api/graph/:caseId/entities?type=xxx */
  getEntities: (caseId, type = '') => {
    const qs = type ? `?type=${type}` : '';
    return apiFetch(`/api/graph/${caseId}/entities${qs}`);
  },

  // ── Reports ───────────────────────────────────────────
  /** POST /api/report/:caseId/generate */
  generateReport: (caseId, opts = {}) =>
    apiFetch(`/api/report/${caseId}/generate`, {
      method: 'POST',
      body: JSON.stringify({ include_graph: true, include_evidence: true, include_timeline: true, ...opts }),
    }),

  /** GET /api/report/:caseId/text */
  getTextReport: (caseId) => apiFetch(`/api/report/${caseId}/text`),

  /** GET /api/report/:caseId/json */
  getJsonReport: (caseId) => apiFetch(`/api/report/${caseId}/json`),

  /** GET /api/report/:caseId/list */
  listReports: (caseId) => apiFetch(`/api/report/${caseId}/list`),
};
