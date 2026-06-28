const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
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
  getMe: () => request("/api/auth/me"),
  login: (payload) => request("/api/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  register: (payload) => request("/api/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  changePassword: (payload) => request("/api/auth/change-password", { method: "POST", body: JSON.stringify(payload) }),
  logout: () => request("/api/auth/logout", { method: "POST" }),
  getTags: () => request("/api/tags"),
  createTag: (payload) => request("/api/tags", { method: "POST", body: JSON.stringify(payload) }),
  updateTag: (id, payload) => request(`/api/tags/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteTag: (id) => request(`/api/tags/${id}`, { method: "DELETE" }),
  generateBrief: () => request("/api/generate-brief", { method: "POST" }),
  getGenerateProgress: () => request("/api/generate-progress"),
  getBriefs: () => request("/api/briefs"),
  getBrief: (date) => request(`/api/briefs/${date}`),
  getStocks: () => request("/api/stocks")
};
