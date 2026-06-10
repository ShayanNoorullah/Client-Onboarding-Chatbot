const ADMIN_PAGES = {
  "dashboard.html": { id: "dashboard", title: "Dashboard", load: loadDashboard },
  "users.html": { id: "users", title: "Users", load: loadUsers },
  "briefs.html": { id: "briefs", title: "Briefs", load: loadBriefs },
  "sessions.html": { id: "sessions", title: "Chats", load: loadSessions },
  "health.html": { id: "health", title: "Health Check", load: loadHealth },
};

function mountPageTemplate() {
  const tpl = document.getElementById("pageTemplate");
  const target = document.getElementById("adminContent");
  if (tpl && target) target.appendChild(tpl.content.cloneNode(true));
}

async function loadDashboard() {
  const data = await API.get("/api/admin/dashboard");
  document.getElementById("statUsers").textContent = data.total_users;
  document.getElementById("statActive").textContent = data.active_users_7d;
  document.getElementById("statSessions").textContent = data.total_sessions;
  document.getElementById("statBriefs").textContent = data.completed_briefs;

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
      recentBody.innerHTML += `<tr>
        <td>${s.session_id.slice(0, 8)}…</td>
        <td>${s.stage}</td>
        <td>${s.project_type || "—"}</td>
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

async function loadUsers() {
  const data = await API.get("/api/admin/users");
  const body = document.getElementById("usersTable");
  body.innerHTML = "";
  (data.users || []).forEach((u) => {
    body.innerHTML += `<tr>
      <td>${u.full_name}</td>
      <td>${u.email}</td>
      <td><span class="badge-admin role-${u.role}">${u.role}</span></td>
      <td>${u.is_active ? "Active" : "Inactive"}</td>
      <td>
        <button class="btn-admin-sm danger" onclick="deactivateUser('${u.id}')">Deactivate</button>
      </td>
    </tr>`;
  });
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
    body.innerHTML += `<tr>
      <td>${b.ref_id}</td>
      <td>${b.client_name}</td>
      <td>${new Date(b.created_at).toLocaleString()}</td>
      <td>
        <a href="${b.download_url}" class="btn-admin-sm">Download</a>
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
    tr.innerHTML = `
      <td>${s.session_id.slice(0, 8)}…</td>
      <td>${s.user_id?.slice(0, 8) || "—"}…</td>
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
  const data = await API.get("/health");
  const statusEl = document.getElementById("healthStatus");
  if (statusEl) {
    statusEl.textContent = data.status;
    statusEl.className = "value " + (data.status === "ok" ? "health-ok" : "health-degraded");
  }
  document.getElementById("healthVersion").textContent = data.version || "—";

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

  initAdminLayout(page.id, page.title);
  mountPageTemplate();

  const searchEl = document.getElementById("adminSessionSearch");
  if (searchEl) {
    searchEl.addEventListener("input", (e) => {
      adminSessionSearch = e.target.value;
      clearTimeout(adminSessionSearchTimer);
      adminSessionSearchTimer = setTimeout(() => loadSessions().catch(console.error), 200);
    });
  }

  await page.load();
});
