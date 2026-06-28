const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      // Keep the generic status message.
    }
    throw new Error(detail);
  }

  return response.json();
}

export const api = {
  getTags: () => request("/api/tags"),
  generateBrief: () => request("/api/generate-brief", { method: "POST" }),
  getBriefs: () => request("/api/briefs"),
  getBrief: (date) => request(`/api/briefs/${date}`),
  getStocks: () => request("/api/stocks")
};
