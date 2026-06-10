const AUTH_USER_CACHE_KEY = "ati_auth_user";

const API = {
  async request(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    if (options.body != null && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }
    const res = await fetch(path, {
      credentials: "include",
      headers,
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
  patch: (path, body) => API.request(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: (path) => API.request(path, { method: "DELETE" }),
};

function cacheAuthUser(user) {
  if (user?.id) {
    sessionStorage.setItem(AUTH_USER_CACHE_KEY, JSON.stringify(user));
  }
}

function readCachedAuthUser() {
  try {
    const raw = sessionStorage.getItem(AUTH_USER_CACHE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function clearAuthSession(userId) {
  sessionStorage.removeItem(AUTH_USER_CACHE_KEY);
  localStorage.removeItem("ati_session_id");
  if (userId) {
    localStorage.removeItem(`ati_session_id_${userId}`);
  }
}

async function fetchAuthUser() {
  try {
    const res = await fetch("/api/auth/me", {
      method: "GET",
      credentials: "include",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) {
      clearAuthSession(readCachedAuthUser()?.id);
      return null;
    }
    const data = await res.json();
    const user = data.user || null;
    if (user) {
      cacheAuthUser(user);
    } else {
      clearAuthSession();
    }
    return user;
  } catch {
    return readCachedAuthUser();
  }
}

async function getCurrentUserOptional() {
  const live = await fetchAuthUser();
  if (live) return live;
  return readCachedAuthUser();
}

async function requireAuth(redirect = "/login.html") {
  const user = await getCurrentUserOptional();
  if (!user) {
    window.location.href = redirect;
    return null;
  }
  cacheAuthUser(user);
  return user;
}

async function logoutUser() {
  const cached = readCachedAuthUser();
  try {
    await API.post("/api/auth/logout", {});
  } catch {
    /* still clear local session state */
  }
  clearAuthSession(cached?.id);
}

function homePathForUser(user) {
  if (!user) return "/login.html";
  return user.role === "admin" ? "/admin/dashboard.html" : "/chat.html";
}
