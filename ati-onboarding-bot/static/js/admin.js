const ADMIN_PAGES = {
  "dashboard.html": {
    id: "dashboard", title: "Dashboard", load: loadDashboard,
    breadcrumbs: [{ label: "Dashboard" }],
  },
  "users.html": {
    id: "settings-users", title: "Users", load: loadUsers,
    breadcrumbs: [{ label: "Dashboard", href: "/admin/dashboard.html" }, { label: "Settings" }, { label: "User" }],
  },
  "briefs.html": {
    id: "briefs", title: "Briefs", load: loadBriefs,
    breadcrumbs: [{ label: "Dashboard", href: "/admin/dashboard.html" }, { label: "Pipeline" }, { label: "Briefs" }],
  },
  "sessions.html": {
    id: "sessions", title: "Onboarding Sessions", load: loadSessions,
    breadcrumbs: [{ label: "Dashboard", href: "/admin/dashboard.html" }, { label: "Pipeline" }, { label: "Sessions" }],
  },
  "health.html": {
    id: "health", title: "Health Check", load: loadHealth,
    breadcrumbs: [{ label: "Dashboard", href: "/admin/dashboard.html" }, { label: "Health" }],
  },
};

function mountPageTemplate() {
  const tpl = document.getElementById("pageTemplate");
  const target = document.getElementById("adminContent");
  if (tpl && target) target.appendChild(tpl.content.cloneNode(true));
}

let dashboardRefreshTimer = null;

async function loadDashboard() {
  const statIds = [
    "statUsers", "statActive", "statSessions", "statBriefs",
    "statCompletion", "statConsent", "statNewUsers", "statActiveSessions",
    "statSessionsToday", "statBriefs7d", "statRoles", "statSmtp",
  ];
  AdminUtils.setStatsLoading(statIds);

  let data;
  try {
    data = await API.get("/api/admin/dashboard");
  } catch (e) {
    AdminUtils.showToast(AdminUtils.formatApiError(e), "error");
    statIds.forEach((id) => AdminUtils.setStatValue(id, "-"));
    return;
  }

  AdminUtils.setStatValue("statUsers", data.total_users_active ?? data.total_users);
  AdminUtils.setStatValue("statActive", data.active_users_7d);
  AdminUtils.setStatValue("statSessions", data.total_sessions);
  AdminUtils.setStatValue("statBriefs", data.completed_briefs);
  AdminUtils.setStatValue("statCompletion", `${data.completion_rate ?? 0}%`);
  AdminUtils.setStatValue("statConsent", `${data.consent_rate ?? 0}%`);
  AdminUtils.setStatValue("statNewUsers", data.new_users_7d ?? 0);
  AdminUtils.setStatValue("statActiveSessions", data.active_sessions_24h ?? 0);
  AdminUtils.setStatValue("statSessionsToday", data.sessions_today ?? 0);
  AdminUtils.setStatValue("statBriefs7d", data.briefs_7d ?? 0);
  AdminUtils.setStatValue("statRoles", data.total_roles ?? 0);
  AdminUtils.setStatValue(
    "statSmtp",
    data.smtp_configured
      ? '<span class="smtp-status-ok">Configured</span>'
      : '<span class="smtp-status-missing">Not Set</span>',
    true,
  );

  const roleBody = document.getElementById("roleTable");
  if (roleBody) {
    roleBody.innerHTML = "";
    const roles = data.users_by_role || {};
    Object.entries(roles).forEach(([role, count]) => {
      roleBody.innerHTML += `<tr><td>${role}</td><td>${count}</td></tr>`;
    });
  }

  const metrics = data.agent_metrics || {};
  const metricsEl = document.getElementById("agentMetricsTable");
  if (metricsEl) {
    metricsEl.innerHTML = `
      <tr><td>Turn latency p50</td><td>${metrics.turn_latency_p50_ms || 0} ms</td></tr>
      <tr><td>Turn latency p95</td><td>${metrics.turn_latency_p95_ms || 0} ms</td></tr>
      <tr><td>Fallback rate</td><td>${metrics.fallback_rate_pct || 0}%</td></tr>
      <tr><td>Avg turns/brief</td><td>${data.avg_turns_to_brief || 0}</td></tr>`;
  }

  const activityBody = document.getElementById("activityTable");
  if (activityBody) {
    activityBody.innerHTML = "";
    (data.activity_by_day || []).forEach((row) => {
      activityBody.innerHTML += `<tr><td>${row.date}</td><td>${row.sessions}</td><td>${row.briefs}</td></tr>`;
    });
  }

  const stageBody = document.getElementById("stageTable");
  if (stageBody) {
    stageBody.innerHTML = "";
    Object.entries(data.sessions_by_stage || {}).forEach(([stage, count]) => {
      stageBody.innerHTML += `<tr><td>${stage}</td><td>${count}</td></tr>`;
    });
  }

  const recentBody = document.getElementById("recentTable");
  if (recentBody) {
    recentBody.innerHTML = "";
    (data.recent_sessions || []).forEach((s) => {
      const userCell = s.user_email
        ? `<a href="/admin/settings-users.html?search=${encodeURIComponent(s.user_email)}">${s.user_display || s.user_name}</a>`
        : (s.user_display || "—");
      recentBody.innerHTML += `<tr>
        <td>${s.session_id.slice(0, 8)}…</td>
        <td>${userCell}</td>
        <td>${s.stage}</td>
        <td>${s.done ? "Yes" : "No"}</td>
        <td>${new Date(s.updated_at).toLocaleString()}</td>
      </tr>`;
    });
  }

  const ptBody = document.getElementById("projectTypeTable");
  if (ptBody) {
    ptBody.innerHTML = "";
    Object.entries(data.project_types || {}).forEach(([pt, count]) => {
      ptBody.innerHTML += `<tr><td>${pt}</td><td>${count}</td></tr>`;
    });
  }
}

let adminUserSearch = "";
let adminUserSearchTimer = null;
let currentAdminUser = null;

function adminUsersUrl() {
  const q = adminUserSearch.trim();
  return q ? `/api/admin/users?q=${encodeURIComponent(q)}` : "/api/admin/users";
}

async function loadUsers() {
  const data = await API.get(adminUsersUrl());
  const body = document.getElementById("usersTable");
  body.innerHTML = "";
  (data.users || []).forEach((u) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${u.full_name}</td>
      <td>${u.email}</td>
      <td><span class="badge-admin role-${u.role}">${u.role}</span></td>
      <td>${u.is_active ? "Active" : "Inactive"}</td>
      <td class="admin-actions-cell"></td>`;
    const actions = tr.querySelector(".admin-actions-cell");
    const isSelf = currentAdminUser && u.id === currentAdminUser.id;

    if (!isSelf && u.is_active) {
      if (u.role === "user") {
        const promoteBtn = document.createElement("button");
        promoteBtn.className = "btn-admin-sm";
        promoteBtn.textContent = "Make admin";
        promoteBtn.onclick = () => changeUserRole(u.id, "admin", u.full_name);
        actions.appendChild(promoteBtn);
      } else {
        const demoteBtn = document.createElement("button");
        demoteBtn.className = "btn-admin-sm";
        demoteBtn.textContent = "Remove admin";
        demoteBtn.onclick = () => changeUserRole(u.id, "user", u.full_name);
        actions.appendChild(demoteBtn);
      }
    }

    if (!isSelf && u.is_active) {
      const deactivateBtn = document.createElement("button");
      deactivateBtn.className = "btn-admin-sm danger";
      deactivateBtn.textContent = "Deactivate";
      deactivateBtn.onclick = () => deactivateUser(u.id);
      actions.appendChild(deactivateBtn);
    }

    body.appendChild(tr);
  });
}

async function changeUserRole(id, role, name) {
  const action = role === "admin" ? "grant admin access to" : "remove admin role from";
  if (!confirm(`Are you sure you want to ${action} ${name}?`)) return;
  await API.put(`/api/admin/users/${id}`, { role });
  loadUsers();
}

async function deactivateUser(id) {
  if (!confirm("Deactivate this user?")) return;
  await API.delete(`/api/admin/users/${id}`);
  loadUsers();
}

async function loadBriefs() {
  const data = await API.get("/api/admin/briefs");
  const body = document.getElementById("briefsTable");
  body.innerHTML = "";
  (data.briefs || []).forEach((b) => {
    const base = b.download_url.split("?")[0];
    body.innerHTML += `<tr>
      <td>${b.ref_id}</td>
      <td>${b.client_name}</td>
      <td>${new Date(b.created_at).toLocaleString()}</td>
      <td class="admin-actions-cell">
        <a href="${base}?format=md" class="btn-admin-sm">MD</a>
        <a href="${base}?format=txt" class="btn-admin-sm">TXT</a>
        <a href="${base}?format=pdf" class="btn-admin-sm">PDF</a>
        <button class="btn-admin-sm danger" onclick="deleteBrief('${b.id}')">Delete</button>
      </td>
    </tr>`;
  });
}

async function deleteBrief(id) {
  if (!confirm("Delete this brief?")) return;
  await API.delete(`/api/admin/briefs/${id}`);
  loadBriefs();
}

let adminSessionSearch = "";
let adminSessionSearchTimer = null;

function adminSessionsUrl() {
  const q = adminSessionSearch.trim();
  return q ? `/api/admin/sessions?q=${encodeURIComponent(q)}` : "/api/admin/sessions";
}

async function loadSessions() {
  const data = await API.get(adminSessionsUrl());
  const body = document.getElementById("sessionsTable");
  body.innerHTML = "";
  (data.sessions || []).forEach((s) => {
    const tr = document.createElement("tr");
    const userLabel = s.user_display || s.user_email || (s.user_id ? `${s.user_id.slice(0, 8)}…` : "—");
    const userCell = s.user_email
      ? `<a href="/admin/settings-users.html?search=${encodeURIComponent(s.user_email)}">${userLabel}</a>`
      : userLabel;
    tr.innerHTML = `
      <td>${s.session_id.slice(0, 8)}…</td>
      <td>${userCell}</td>
      <td>${s.display_name || "New chat"}</td>
      <td>${s.stage}</td>
      <td>${s.pinned ? "Yes" : "No"}</td>
      <td>${s.consent_given ? "Yes" : "No"}</td>
      <td>${s.done ? "Yes" : "No"}</td>
      <td>${new Date(s.updated_at).toLocaleString()}</td>
      <td class="admin-actions-cell"></td>`;
    const actions = tr.querySelector(".admin-actions-cell");

    const pinBtn = document.createElement("button");
    pinBtn.className = "btn-admin-sm";
    pinBtn.textContent = s.pinned ? "Unpin" : "Pin";
    pinBtn.onclick = () => toggleAdminPin(s.session_id, s.pinned);

    const renameBtn = document.createElement("button");
    renameBtn.className = "btn-admin-sm";
    renameBtn.textContent = "Rename";
    renameBtn.onclick = () => renameAdminSession(s.session_id, s.title || s.display_name || "");

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "btn-admin-sm danger";
    deleteBtn.textContent = "Delete";
    deleteBtn.onclick = () => deleteSession(s.session_id);

    actions.append(pinBtn, renameBtn, deleteBtn);
    body.appendChild(tr);
  });
}

async function toggleAdminPin(id, pinned) {
  await API.patch(`/api/admin/sessions/${id}`, { pinned: !pinned });
  loadSessions();
}

async function renameAdminSession(id, currentTitle) {
  const next = window.prompt("Rename chat", currentTitle || "");
  if (next === null) return;
  const title = next.trim();
  if (!title) {
    alert("Chat name cannot be empty.");
    return;
  }
  await API.patch(`/api/admin/sessions/${id}`, { title });
  loadSessions();
}

async function deleteSession(id) {
  if (!confirm("Delete this chat?")) return;
  await API.delete(`/api/admin/sessions/${id}`);
  loadSessions();
}

async function loadHealth() {
  AdminUtils.setStatsLoading(["healthStatus", "healthVersion"]);
  const data = await API.get("/health");
  const statusEl = document.getElementById("healthStatus");
  if (statusEl) {
    AdminUtils.setStatValue("healthStatus", data.status);
    statusEl.className = "value " + (data.status === "ok" ? "health-ok" : "health-degraded");
  }
  AdminUtils.setStatValue("healthVersion", data.version || "—");

  const ollama = data.ollama || {};
  const ollamaBody = document.getElementById("ollamaTable");
  if (ollamaBody) {
    ollamaBody.innerHTML = `
      <tr><td>Reachable</td><td class="${ollama.ollama_reachable ? "health-ok" : "health-error"}">${ollama.ollama_reachable ? "Yes" : "No"}</td></tr>
      <tr><td>Models pulled</td><td>${(ollama.models || []).join(", ") || "—"}</td></tr>
      <tr><td>Missing</td><td>${(ollama.missing || []).join(", ") || "None"}</td></tr>
    `;
  }
  document.getElementById("healthRaw").textContent = JSON.stringify(data, null, 2);
}

document.addEventListener("DOMContentLoaded", async () => {
  const page = ADMIN_PAGES[location.pathname.split("/").pop() || ""];
  if (!page) return;

  const user = await requireAdmin();
  if (!user) return;
  currentAdminUser = user;

  initAdminLayout(page.id, page.title, page.breadcrumbs || []);
  mountPageTemplate();

  if (page.id === "dashboard") {
    const actions = document.getElementById("adminPageActions");
    if (actions) {
      actions.innerHTML = `<button type="button" class="btn btn-outline-secondary btn-sm" id="refreshDashboardBtn"><i class="fa fa-rotate"></i> Refresh</button>`;
      document.getElementById("refreshDashboardBtn")?.addEventListener("click", () => {
        loadDashboard().catch((e) => AdminUtils.showToast(AdminUtils.formatApiError(e), "error"));
      });
      if (dashboardRefreshTimer) clearInterval(dashboardRefreshTimer);
      dashboardRefreshTimer = setInterval(() => {
        if (document.visibilityState === "visible") {
          loadDashboard().catch(() => {});
        }
      }, 60000);
    }
  }

  const searchEl = document.getElementById("adminSessionSearch");
  if (searchEl) {
    searchEl.addEventListener("input", (e) => {
      adminSessionSearch = e.target.value;
      clearTimeout(adminSessionSearchTimer);
      adminSessionSearchTimer = setTimeout(() => loadSessions().catch(console.error), 200);
    });
  }

  const userSearchEl = document.getElementById("adminUserSearch");
  if (userSearchEl) {
    userSearchEl.addEventListener("input", (e) => {
      adminUserSearch = e.target.value;
      clearTimeout(adminUserSearchTimer);
      adminUserSearchTimer = setTimeout(() => loadUsers().catch(console.error), 200);
    });
  }

  await page.load();
});
