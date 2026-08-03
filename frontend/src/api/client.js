/**
 * Thin fetch wrapper around the FactoryPulse AI backend. Every function here
 * maps 1:1 to a FastAPI route, so a component never constructs a URL or
 * touches `fetch` directly -- swapping REST for GraphQL later only means
 * editing this one file.
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Request to ${path} failed (${res.status}): ${body}`);
  }
  return res.json();
}

export const api = {
  listMachines: () => request("/machines"),
  getMachine: (machineId) => request(`/machines/${machineId}`),
  predict: (payload) =>
    request("/predictions/predict", { method: "POST", body: JSON.stringify(payload) }),
  executiveDashboard: () => request("/dashboard/executive"),
  riskDashboard: () => request("/dashboard/risk"),
  maintenanceReport: () => request("/reports/maintenance"),
  askChat: (question) =>
    request("/chat/ask", { method: "POST", body: JSON.stringify({ question }) }),
};
