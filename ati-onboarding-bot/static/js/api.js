const API = {
  async request(path, options = {}) {
    const res = await fetch(path, {
      credentials: "include",
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      let detail = data.detail || data.message || "Request failed";
      if (Array.isArray(detail)) {
        detail = detail.map((d) => (typeof d === "string" ? d : d.msg || JSON.stringify(d))).join(", ");
      }
      throw new Error(detail);
    }
    return data;
  },
  get: (path) => API.request(path),
  post: (path, body) => API.request(path, { method: "POST", body: JSON.stringify(body) }),
  put: (path, body) => API.request(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: (path) => API.request(path, { method: "DELETE" }),
};

async function requireAuth(redirect = "/login.html") {
  try {
    const data = await API.get("/api/auth/me");
    return data.user;
  } catch {
    window.location.href = redirect;
    return null;
  }
}
