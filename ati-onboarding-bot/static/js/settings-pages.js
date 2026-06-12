let editingId = null, moduleFilter = "", modulesCache = [];

async function loadModules() {
  const data = await AdminUtils.apiGet("/api/admin/settings/modules");
  modulesCache = data.modules || [];
  const sel = document.getElementById("filterModule");
  const modSel = document.getElementById("pageModule");
  const opts = modulesCache.map((m) => `<option value="${m.name}">${m.name}</option>`).join("");
  if (sel) sel.innerHTML = `<option value="">All Modules</option>${opts}`;
  if (modSel) modSel.innerHTML = opts;
}

async function loadPages() {
  const tbody = document.getElementById("pagesTableBody");
  tbody.innerHTML = `<tr><td colspan="6" class="admin-loading"><div class="spinner-border spinner-border-sm"></div></td></tr>`;
  try {
    const q = moduleFilter ? `?module_name=${encodeURIComponent(moduleFilter)}` : "";
    const data = await AdminUtils.apiGet(`/api/admin/settings/pages${q}`);
    const pages = data.pages || [];
    tbody.innerHTML = pages.length ? pages.map((p) => `<tr>
      <td><button class="action-btn" data-edit="${p.id}">Edit</button>
      <button class="action-btn ms-1" data-del="${p.id}">Delete</button></td>
      <td>${p.module_name}</td><td>${p.page_name}</td><td>${p.route}</td>
      <td>${p.sort_order}</td><td>${p.is_active ? "✓" : "×"}</td></tr>`).join("")
      : `<tr><td colspan="6" class="admin-empty-state">No records found</td></tr>`;
    document.querySelectorAll("[data-edit]").forEach((b) => b.addEventListener("click", () => openModal(b.dataset.edit, pages)));
    document.querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", async () => {
      if (!await AdminUtils.showConfirm("Delete this page?")) return;
      await AdminUtils.apiDelete(`/api/admin/settings/pages/${b.dataset.del}`);
      AdminUtils.showToast("Deleted"); loadPages();
    }));
  } catch (e) { tbody.innerHTML = `<tr><td colspan="6"><div class="alert alert-danger">${e.message}</div></td></tr>`; }
}

function openModal(id, pages) {
  editingId = id;
  document.getElementById("pageForm").reset();
  if (id) {
    const p = pages.find((x) => x.id === id);
    if (p) {
      document.getElementById("pageModule").value = p.module_name;
      document.getElementById("pageName").value = p.page_name;
      document.getElementById("pageRoute").value = p.route;
      document.getElementById("pageSort").value = p.sort_order;
      document.getElementById("pageActive").checked = p.is_active;
    }
  }
  new bootstrap.Modal(document.getElementById("pageModal")).show();
}

async function savePage() {
  const body = { module_name: document.getElementById("pageModule").value, page_name: document.getElementById("pageName").value,
    route: document.getElementById("pageRoute").value, sort_order: +document.getElementById("pageSort").value,
    is_active: document.getElementById("pageActive").checked };
  try {
    if (editingId) await AdminUtils.apiPut(`/api/admin/settings/pages/${editingId}`, body);
    else await AdminUtils.apiPost("/api/admin/settings/pages", body);
    bootstrap.Modal.getInstance(document.getElementById("pageModal"))?.hide();
    AdminUtils.showToast("Page saved"); loadPages();
  } catch (e) { AdminUtils.showToast(e.message, "error"); }
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("settings-pages", "APPLICATION PAGE", [{ label: "Dashboard", href: "/admin/dashboard.html" }, { label: "Settings" }, { label: "Application Page" }]);
  document.getElementById("adminPageActions").innerHTML = `<button class="btn-admin-primary" id="addPageBtn">+ Add Page</button>`;
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  await loadModules();
  document.getElementById("filterModule").addEventListener("change", (e) => { moduleFilter = e.target.value; loadPages(); });
  document.getElementById("addPageBtn").addEventListener("click", () => openModal(null, []));
  document.getElementById("savePageBtn").addEventListener("click", savePage);
  loadPages();
});
