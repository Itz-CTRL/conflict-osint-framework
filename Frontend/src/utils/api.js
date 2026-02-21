// src/utils/api.js
const API = 'http://127.0.0.1:5000';

export async function apiFetch(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => apiFetch('/api/health'),
  getInvestigations: () => apiFetch('/api/investigations'),
  createInvestigation: (username) =>
    apiFetch('/api/investigations', {
      method: 'POST',
      body: JSON.stringify({ username }),
    }),
  runInvestigation: (id) =>
    apiFetch(`/api/investigate/${id}`, { method: 'POST' }),
  getInvestigation: (id) => apiFetch(`/api/investigations/${id}`),
  deleteInvestigation: (id) =>
    apiFetch(`/api/investigations/${id}`, { method: 'DELETE' }),
};
