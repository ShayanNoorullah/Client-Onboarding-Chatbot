let currentUser = null;

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
        <td>${s.session_id.slice(0,8)}…</td>
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
      <td><span class="badge bg-${u.role === "admin" ? "danger" : "secondary"}">${u.role}</span></td>
      <td>${u.is_active ? "Active" : "Inactive"}</td>
      <td>
        <button class="btn btn-sm btn-outline-danger" onclick="deactivateUser('${u.id}')">Deactivate</button>
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
        <a href="${b.download_url}" class="btn btn-sm btn-outline-primary">Download</a>
        <button class="btn btn-sm btn-outline-danger" onclick="deleteBrief('${b.id}')">Delete</button>
      </td>
    </tr>`;
  });
}

async function deleteBrief(id) {
  if (!confirm("Delete this brief?")) return;
  await API.delete(`/api/admin/briefs/${id}`);
  loadBriefs();
}

document.addEventListener("DOMContentLoaded", async () => {
  currentUser = await requireAuth("/login.html");
  if (!currentUser || currentUser.role !== "admin") {
    window.location.href = "/chat.html";
    return;
  }
  document.getElementById("logoutBtn")?.addEventListener("click", async () => {
    await API.post("/api/auth/logout", {});
    window.location.href = "/login.html";
  });
  if (document.getElementById("statUsers")) loadDashboard();
  if (document.getElementById("usersTable")) loadUsers();
  if (document.getElementById("briefsTable")) loadBriefs();
});
