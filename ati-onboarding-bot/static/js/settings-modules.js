let editingId = null;

async function loadModules() {
  const tbody = document.getElementById("modulesTableBody");
  tbody.innerHTML = `<tr><td colspan="6" class="admin-loading"><div class="spinner-border spinner-border-sm"></div></td></tr>`;
  try {
    const data = await AdminUtils.apiGet("/api/admin/settings/modules");
    const mods = data.modules || [];
    tbody.innerHTML = mods.length ? mods.map((m) => `<tr>
      <td><button class="action-btn" data-edit="${m.id}">Edit</button>
      <button class="action-btn ms-1" data-del="${m.id}">Delete</button></td>
      <td>${m.name}</td><td><i class="${m.icon}"></i> ${m.icon}</td>
      <td>${m.sort_order}</td><td>${m.created_by || "—"}</td>
      <td>${m.is_active ? "✓" : "×"}</td></tr>`).join("")
      : `<tr><td colspan="6" class="admin-empty-state">No records found</td></tr>`;
    document.querySelectorAll("[data-edit]").forEach((b) => b.addEventListener("click", () => openModal(b.dataset.edit)));
    document.querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", async () => {
      if (!await AdminUtils.showConfirm("Delete this module?")) return;
      try { await AdminUtils.apiDelete(`/api/admin/settings/modules/${b.dataset.del}`); AdminUtils.showToast("Deleted"); loadModules(); }
      catch (e) { AdminUtils.showToast(e.message, "error"); }
    }));
  } catch (e) { tbody.innerHTML = `<tr><td colspan="6"><div class="alert alert-danger">${e.message}</div></td></tr>`; }
}

async function openModal(id) {
  editingId = id;
  document.getElementById("modForm").reset();
  document.getElementById("modIconPreview").className = "fa fa-th-large";
  if (id) {
    const data = await AdminUtils.apiGet("/api/admin/settings/modules");
    const m = (data.modules || []).find((x) => x.id === id);
    if (m) {
      document.getElementById("modName").value = m.name;
      document.getElementById("modIcon").value = m.icon;
      document.getElementById("modSort").value = m.sort_order;
      document.getElementById("modActive").checked = m.is_active;
      document.getElementById("modIconPreview").className = m.icon;
    }
  }
  new bootstrap.Modal(document.getElementById("modModal")).show();
}

async function saveModule() {
  const body = { name: document.getElementById("modName").value, icon: document.getElementById("modIcon").value,
    sort_order: +document.getElementById("modSort").value, is_active: document.getElementById("modActive").checked };
  try {
    if (editingId) await AdminUtils.apiPut(`/api/admin/settings/modules/${editingId}`, body);
    else await AdminUtils.apiPost("/api/admin/settings/modules", body);
    bootstrap.Modal.getInstance(document.getElementById("modModal"))?.hide();
    AdminUtils.showToast("Module saved"); loadModules();
  } catch (e) { AdminUtils.showToast(e.message, "error"); }
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("settings-modules", "APPLICATION MODULE", [{ label: "Dashboard", href: "/admin/dashboard.html" }, { label: "Settings" }, { label: "Application Module" }]);
  document.getElementById("adminPageActions").innerHTML = `<button class="btn-admin-primary" id="addModBtn">+ Add Module</button>`;
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  document.getElementById("addModBtn").addEventListener("click", () => openModal(null));
  document.getElementById("saveModBtn").addEventListener("click", saveModule);
  document.getElementById("modIcon").addEventListener("input", (e) => { document.getElementById("modIconPreview").className = e.target.value || "fa fa-th-large"; });
  loadModules();
});
