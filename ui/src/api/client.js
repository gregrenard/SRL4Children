// API client for SRL4C backend
const API_BASE = '/api';

const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Request failed');
  }
  return response.json();
};

export const api = {
  // Endpoints
  getEndpoints: () => fetch(`${API_BASE}/endpoints`).then(handleResponse),
  createEndpoint: (data) => fetch(`${API_BASE}/endpoints`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(handleResponse),
  deleteEndpoint: (id) => fetch(`${API_BASE}/endpoints/${id}`, { method: 'DELETE' }).then(handleResponse),
  testEndpoint: (id) => fetch(`${API_BASE}/endpoints/${id}/test`, { method: 'POST' }).then(handleResponse),

  // Attacks
  getAttacks: () => fetch(`${API_BASE}/attacks`).then(handleResponse),
  getAttack: (id) => fetch(`${API_BASE}/attacks/${id}`).then(handleResponse),
  createAttack: (data) => fetch(`${API_BASE}/attacks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(handleResponse),
  deleteAttack: (id) => fetch(`${API_BASE}/attacks/${id}`, { method: 'DELETE' }).then(handleResponse),

  // Scores
  getScores: () => fetch(`${API_BASE}/scores`).then(handleResponse),
  getScore: (id) => fetch(`${API_BASE}/scores/${id}`).then(handleResponse),
  createScore: (data) => fetch(`${API_BASE}/scores`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(handleResponse),
  getScoreReport: (id) => fetch(`${API_BASE}/scores/${id}/report`).then(handleResponse),
  getScoreFailures: (id) => fetch(`${API_BASE}/scores/${id}/failures`).then(handleResponse),
  deleteScore: (id) => fetch(`${API_BASE}/scores/${id}`, { method: 'DELETE' }).then(handleResponse),

  // Guardrails
  getGuardrails: () => fetch(`${API_BASE}/guardrails`).then(handleResponse),
  getGuardrail: (id) => fetch(`${API_BASE}/guardrails/${id}`).then(handleResponse),
  createGuardrail: (data) => fetch(`${API_BASE}/guardrails`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(handleResponse),
  exportGuardrail: (id) => fetch(`${API_BASE}/guardrails/${id}/export`).then(handleResponse),
  deleteGuardrail: (id) => fetch(`${API_BASE}/guardrails/${id}`, { method: 'DELETE' }).then(handleResponse),

  // Reference data
  getDatasets: () => fetch(`${API_BASE}/datasets`).then(handleResponse),
  getDatasetPrompts: (name, page = 1, pageSize = 50) =>
    fetch(`${API_BASE}/datasets/${name}/prompts?page=${page}&page_size=${pageSize}`).then(handleResponse),
  getPrinciples: () => fetch(`${API_BASE}/principles`).then(handleResponse),

  // Logs
  getLogs: (limit = 50) => fetch(`${API_BASE}/logs?limit=${limit}`).then(handleResponse),
};

export default api;
