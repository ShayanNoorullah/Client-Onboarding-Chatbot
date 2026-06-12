let editingId = null, pageFilter = "", pagesCache = [];
let actionsPage = 1, actionsLimit = 25, actionsSearch = "", actionModal = null;

async function loadPages() {
  const data = await AdminUtils.apiGet("/api/admin/settings/pages");
  pagesCache = data.pages || [];
  const names = [...new Set(pagesCache.map((p) => p.page_name))];
  const sel = document.getElementById("filterPage");
  const pageSel = document.getElementById("actionPage");
  const opts = names.map((n) => `<option value="${n}">${n}</option>`).join("");
  if (sel) sel.innerHTML = `<option value="">All Pages</option>${opts}`;
  if (pageSel) pageSel.innerHTML = opts;
}

async function loadActions() {
  const tbody = document.getElementById("actionsTableBody");
  tbody.innerHTML = `<tr><td colspan="7" class="admin-loading"><div class="spinner-border spinner-border-sm"></div></td></tr>`;
  try {
    const params = new URLSearchParams({ page: actionsPage, limit: actionsLimit });
    if (pageFilter) params.set("page_name", pageFilter);
    if (actionsSearch) params.set("search", actionsSearch);
    const data = await AdminUtils.apiGet(`/api/admin/settings/actions?${params}`);
    const actions = data.actions || [];
    tbody.innerHTML = actions.length ? actions.map((a) => `<tr>
      <td>
        <button class="action-btn" data-pin="${a.id}" title="Pin">${a.is_pinned ? "📌" : "○"}</button>
        <button class="action-btn" data-edit="${a.id}">Edit</button>
        <button class="action-btn" data-toggle="${a.id}">${a.is_active ? "Disable" : "Enable"}</button>
        <button class="action-btn action-btn-danger" data-del="${a.id}">Delete</button>
      </td>
      <td>${a.page_name}</td><td>${a.action_name}</td><td><code>${a.action_key}</code></td>
      <td>${a.sort_order ?? 0}</td><td>${a.created_by || "—"}</td>
      <td>${a.is_active ? "✓" : "×"}</td></tr>`).join("")
      : `<tr><td colspan="7" class="admin-empty-state">No records found</td></tr>`;
    tbody.querySelectorAll("[data-edit]").forEach((b) => b.addEventListener("click", () => openModal(b.dataset.edit)));
    tbody.querySelectorAll("[data-pin]").forEach((b) => b.addEventListener("click", () => togglePin(b.dataset.pin)));
    tbody.querySelectorAll("[data-toggle]").forEach((b) => b.addEventListener("click", () => toggleActive(b.dataset.toggle)));
    tbody.querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", () => deleteAction(b.dataset.del)));
    AdminUtils.renderPagination(document.getElementById("actionsPagination"), data.page, data.total, data.pages, (p) => {
      actionsPage = p;
      loadActions();
    });
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="alert alert-danger">${AdminUtils.formatApiError(e)}</div></td></tr>`;
  }
}

async function openModal(id) {
  editingId = id;
  document.getElementById("actionForm").reset();
  if (id) {
    const data = await AdminUtils.apiGet(`/api/admin/settings/actions/${id}`);
    const a = data.action;
    document.getElementById("actionPage").value = a.page_name;
    document.getElementById("actionName").value = a.action_name;
    document.getElementById("actionKey").value = a.action_key;
    document.getElementById("actionSort").value = a.sort_order ?? 0;
    document.getElementById("actionPinned").checked = a.is_pinned;
    document.getElementById("actionActive").checked = a.is_active;
  }
  actionModal.show();
}

async function togglePin(id) {
  const data = await AdminUtils.apiGet(`/api/admin/settings/actions/${id}`);
  await AdminUtils.apiPatch(`/api/admin/settings/actions/${id}`, { is_pinned: !data.action.is_pinned });
  loadActions();
}

async function toggleActive(id) {
  const data = await AdminUtils.apiGet(`/api/admin/settings/actions/${id}`);
  await AdminUtils.apiPatch(`/api/admin/settings/actions/${id}`, { is_active: !data.action.is_active });
  loadActions();
}

async function deleteAction(id) {
  if (!await AdminUtils.showConfirm("Delete this action?")) return;
  try {
    await AdminUtils.apiDelete(`/api/admin/settings/actions/${id}`);
    AdminUtils.showToast("Deleted");
    loadActions();
  } catch (e) {
    AdminUtils.showToast(AdminUtils.formatApiError(e), "error");
  }
}

async function saveAction() {
  const form = document.getElementById("actionForm");
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }
  const body = {
    page_name: document.getElementById("actionPage").value,
    action_name: document.getElementById("actionName").value.trim(),
    action_key: document.getElementById("actionKey").value.trim().toLowerCase(),
    sort_order: parseInt(document.getElementById("actionSort").value, 10) || 0,
    is_pinned: document.getElementById("actionPinned").checked,
    is_active: document.getElementById("actionActive").checked,
  };
  try {
    if (editingId) await AdminUtils.apiPut(`/api/admin/settings/actions/${editingId}`, body);
    else await AdminUtils.apiPost("/api/admin/settings/actions", body);
    actionModal.hide();
    AdminUtils.showToast("Action saved");
    loadActions();
  } catch (e) {
    AdminUtils.showToast(AdminUtils.formatApiError(e), "error");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("settings-actions", "APPLICATION ACTION", [
    { label: "Dashboard", href: "/admin/dashboard.html" },
    { label: "Settings" },
    { label: "Application Action" },
  ]);
  document.getElementById("adminPageActions").innerHTML = `<button class="btn-admin-primary" id="addActionBtn">+ Add Action</button>`;
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  actionModal = new bootstrap.Modal(document.getElementById("actionModal"));
  AdminUtils.renderTableControls(document.getElementById("tableControls"), actionsLimit, (n) => {
    actionsLimit = n;
    actionsPage = 1;
    loadActions();
  }, (q) => {
    actionsSearch = q;
    actionsPage = 1;
    loadActions();
  });
  await loadPages();
  document.getElementById("filterPage").addEventListener("change", (e) => {
    pageFilter = e.target.value;
    actionsPage = 1;
    loadActions();
  });
  document.getElementById("addActionBtn").addEventListener("click", () => openModal(null));
  document.getElementById("saveActionBtn").addEventListener("click", saveAction);
  loadActions();
});
