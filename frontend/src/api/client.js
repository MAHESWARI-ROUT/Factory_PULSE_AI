/**
 * Thin fetch wrapper around the FactoryPulse AI backend.
 * Every function here maps 1:1 to a FastAPI route.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

if (!BASE_URL) {
  throw new Error("VITE_API_BASE_URL is not configured");
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
    },
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

  getMachine: (machineId) =>
    request(`/machines/${machineId}`),

  predict: (payload) =>
    request("/predictions/predict", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  executiveDashboard: () =>
    request("/dashboard/executive"),

  riskDashboard: () =>
    request("/dashboard/risk"),

  maintenanceReport: () =>
    request("/reports/maintenance"),

  askChat: (question) =>
    request("/chat/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
};