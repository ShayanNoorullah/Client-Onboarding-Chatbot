let rolesPage = 1, rolesLimit = 10, rolesSearch = "";
let modulesCache = [], pagesCache = [], actionsCache = [], editingRoleId = null;
let roleModal = null;

async function loadModulesAndPages() {
  const mods = await AdminUtils.apiGet("/api/admin/settings/modules");
  modulesCache = mods.modules || [];
  const pgs = await AdminUtils.apiGet("/api/admin/settings/pages");
  pagesCache = pgs.pages || [];
  try {
    const acts = await AdminUtils.apiGet("/api/admin/settings/actions?limit=200");
    actionsCache = acts.actions || [];
  } catch (_) {
    actionsCache = [];
  }
}

function actionsForPage(pageName) {
  const keys = actionsCache
    .filter((a) => a.page_name === pageName && a.is_active)
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || a.action_key.localeCompare(b.action_key));
  if (keys.length) return keys.map((a) => a.action_key);
  return ["view", "insert", "update", "delete"];
}

async function loadRoles() {
  const tbody = document.getElementById("rolesTableBody");
  tbody.innerHTML = `<tr><td colspan="4" class="admin-loading"><div class="spinner-border spinner-border-sm"></div></td></tr>`;
  try {
    const q = rolesSearch ? `&search=${encodeURIComponent(rolesSearch)}` : "";
    const data = await AdminUtils.apiGet(`/api/admin/settings/roles?page=${rolesPage}&limit=${rolesLimit}${q}`);
    const roles = (data.roles || []).slice().sort((a, b) => (a.sort_order ?? 99) - (b.sort_order ?? 99) || a.name.localeCompare(b.name));
    tbody.innerHTML = roles.length ? roles.map((r) => `<tr>
      <td><button class="action-btn" data-edit-role="${r.id}">Edit</button></td>
      <td>${r.name}</td><td>${r.description || "—"}</td>
      <td>${r.is_active ? "✓" : "×"}</td></tr>`).join("")
      : `<tr><td colspan="4" class="admin-empty-state">No records found</td></tr>`;
    document.querySelectorAll("[data-edit-role]").forEach((b) => b.addEventListener("click", () => openRoleDetail(b.dataset.editRole)));
    AdminUtils.renderPagination(document.getElementById("rolesPagination"), data.page, data.total, data.pages, (p) => { rolesPage = p; loadRoles(); });
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="4"><div class="alert alert-danger">${AdminUtils.formatApiError(e)}</div></td></tr>`;
  }
}

function buildPermissionMatrix(existingPermissions) {
  const perms = existingPermissions || {};
  if (!modulesCache.length) {
    return `<p class="text-secondary small">Loading permission modules…</p>`;
  }
  const tabs = modulesCache.map((m, i) => {
    const modPages = pagesCache.filter((p) => p.module_name === m.name);
    const actionKeys = [...new Set(modPages.flatMap((p) => actionsForPage(p.page_name)))];
    const rows = modPages.map((p) => {
      const pp = perms[m.name]?.[p.page_name] || {};
      const pageActions = actionsForPage(p.page_name);
      return `<tr data-module="${m.name}" data-page="${p.page_name}">
        <td>${p.page_name}</td>
        ${pageActions.map((k) =>
          `<td><input type="checkbox" class="perm-cb" data-action="${k}" ${pp[k] ? "checked" : ""}></td>`
        ).join("")}
      </tr>`;
    }).join("");
    const selectAll = actionKeys.map((k) =>
      `<th><input type="checkbox" class="select-all-col" data-module="${m.name}" data-action="${k}"> ${k}</th>`
    ).join("");
    return `<div class="tab-pane fade${i === 0 ? " show active" : ""}" id="tab-${m.name.replace(/\s/g, "")}">
      <table class="permission-matrix table table-sm"><thead><tr><th>Page</th>${selectAll}</tr></thead><tbody>${rows}</tbody></table></div>`;
  }).join("");
  const tabHeaders = modulesCache.map((m, i) =>
    `<li class="nav-item"><button class="nav-link${i === 0 ? " active" : ""}" data-bs-toggle="tab" data-bs-target="#tab-${m.name.replace(/\s/g, "")}">${m.name}</button></li>`
  ).join("");
  return `<ul class="nav nav-tabs permission-tabs">${tabHeaders}</ul><div class="tab-content mt-3">${tabs}</div>`;
}

function setAllPermissions(checked, onlyView = false) {
  document.querySelectorAll("#roleMatrix .perm-cb").forEach((cb) => {
    if (onlyView) cb.checked = cb.dataset.action === "view" && checked;
    else cb.checked = checked;
  });
}

async function openRoleDetail(roleId) {
  editingRoleId = roleId;
  document.getElementById("roleModalTitle").textContent = roleId ? "Edit Role" : "Add Role";
  if (roleId) {
    const data = await AdminUtils.apiGet(`/api/admin/settings/roles/${roleId}`);
    const r = data.role;
    document.getElementById("roleName").value = r.name;
    document.getElementById("roleDesc").value = r.description || "";
    document.getElementById("roleActive").checked = r.is_active;
    document.getElementById("roleMatrix").innerHTML = buildPermissionMatrix(r.permissions);
  } else {
    document.getElementById("roleName").value = "";
    document.getElementById("roleDesc").value = "";
    document.getElementById("roleActive").checked = true;
    document.getElementById("roleMatrix").innerHTML = buildPermissionMatrix({});
  }
  bindMatrixEvents();
  roleModal.show();
}

function bindMatrixEvents() {
  document.querySelectorAll(".select-all-col").forEach((cb) => {
    cb.addEventListener("change", () => {
      const mod = cb.dataset.module;
      const act = cb.dataset.action;
      document.querySelectorAll(`tr[data-module="${mod}"] .perm-cb[data-action="${act}"]`).forEach((c) => { c.checked = cb.checked; });
    });
  });
}

function collectPermissions() {
  const perms = {};
  document.querySelectorAll("#roleMatrix tr[data-module]").forEach((row) => {
    const mod = row.dataset.module;
    const page = row.dataset.page;
    perms[mod] = perms[mod] || {};
    perms[mod][page] = {};
    row.querySelectorAll(".perm-cb").forEach((cb) => { perms[mod][page][cb.dataset.action] = cb.checked; });
  });
  return perms;
}

async function saveRole() {
  const name = document.getElementById("roleName").value.trim();
  if (!name) {
    AdminUtils.showToast("Role name is required", "warning");
    return;
  }
  const body = {
    name,
    description: document.getElementById("roleDesc").value,
    is_active: document.getElementById("roleActive").checked,
    permissions: collectPermissions(),
  };
  try {
    if (editingRoleId) await AdminUtils.apiPut(`/api/admin/settings/roles/${editingRoleId}`, body);
    else await AdminUtils.apiPost("/api/admin/settings/roles", body);
    AdminUtils.showToast("Role saved");
    roleModal.hide();
    loadRoles();
  } catch (e) {
    AdminUtils.showToast(AdminUtils.formatApiError(e), "error");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("settings-roles", "ROLE", [
    { label: "Dashboard", href: "/admin/dashboard.html" },
    { label: "Settings" },
    { label: "Role" },
  ]);
  document.getElementById("adminPageActions").innerHTML = `<button class="btn-admin-primary" id="addRoleBtn">+ Add Role</button>`;
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  roleModal = new bootstrap.Modal(document.getElementById("roleModal"));

  AdminUtils.renderTableControls(document.getElementById("tableControls"), rolesLimit, (n) => {
    rolesLimit = n;
    rolesPage = 1;
    loadRoles();
  }, (q) => {
    rolesSearch = q;
    rolesPage = 1;
    loadRoles();
  });

  document.getElementById("addRoleBtn").addEventListener("click", () => openRoleDetail(null));
  document.getElementById("saveRoleBtn").addEventListener("click", saveRole);
  document.getElementById("permPresetView").addEventListener("click", () => setAllPermissions(true, true));
  document.getElementById("permPresetFull").addEventListener("click", () => setAllPermissions(true, false));
  document.getElementById("permPresetClear").addEventListener("click", () => setAllPermissions(false, false));

  await loadModulesAndPages();
  await loadRoles();
});
