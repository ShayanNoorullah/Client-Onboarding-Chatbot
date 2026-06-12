let usersPage = 1, usersLimit = 10, usersSearch = "", rolesCache = [];

function roleBadge(name) {
  if (name === "Admin") return `<span class="badge-role-admin">${name}</span>`;
  if (name === "Super Admin") return `<span class="badge-role-super">${name}</span>`;
  return `<span class="badge-role-user">${name}</span>`;
}

async function loadRolesDropdown() {
  const data = await AdminUtils.apiGet("/api/admin/settings/roles?limit=100");
  rolesCache = (data.roles || []).sort((a, b) => (a.sort_order ?? 99) - (b.sort_order ?? 99));
  const sel = document.getElementById("userRole");
  if (sel) sel.innerHTML = rolesCache.map((r) => `<option value="${r.name}">${r.name}</option>`).join("");
}

async function loadUsers() {
  const tbody = document.getElementById("usersTableBody");
  const pagination = document.getElementById("usersPagination");
  tbody.innerHTML = `<tr><td colspan="5" class="admin-loading"><div class="spinner-border spinner-border-sm"></div> Loading...</td></tr>`;
  try {
    const q = usersSearch ? `&search=${encodeURIComponent(usersSearch)}` : "";
    const data = await AdminUtils.apiGet(`/api/admin/settings/users?page=${usersPage}&limit=${usersLimit}${q}`);
    const users = data.users || [];
    if (!users.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="admin-empty-state"><i class="fa fa-inbox"></i><p>No records found</p></td></tr>`;
    } else {
      tbody.innerHTML = users.map((u) => {
        const uname = u.username || u.email.split("@")[0];
        return `<tr>
          <td><div style="position:relative">
            <button class="action-btn" data-action-menu="${u.id}">Action ▼</button>
            <div class="action-dropdown" id="menu-${u.id}">
              <button data-edit="${u.id}">Edit</button>
              <button data-toggle="${u.id}" data-active="${u.is_active}">${u.is_active ? "Deactivate" : "Activate"}</button>
              <button class="danger" data-delete="${u.id}">Delete</button>
            </div></div></td>
          <td>${u.full_name}</td>
          <td>${roleBadge(u.role_name || "User")}</td>
          <td>${uname}</td>
          <td>${u.is_active ? '<span class="smtp-status-ok">✓</span>' : '<span class="smtp-status-missing">×</span>'}</td>
        </tr>`;
      }).join("");
      bindUserActions();
    }
    AdminUtils.renderPagination(pagination, data.page, data.total, data.pages, (p) => { usersPage = p; loadUsers(); });
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5"><div class="alert alert-danger">${e.message}</div></td></tr>`;
  }
}

function bindUserActions() {
  document.querySelectorAll("[data-action-menu]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      document.querySelectorAll(".action-dropdown").forEach((d) => d.classList.remove("show"));
      document.getElementById(`menu-${btn.dataset.actionMenu}`)?.classList.toggle("show");
    });
  });
  document.addEventListener("click", () => document.querySelectorAll(".action-dropdown").forEach((d) => d.classList.remove("show")), { once: true });
  document.querySelectorAll("[data-edit]").forEach((btn) => btn.addEventListener("click", () => openEditModal(btn.dataset.edit)));
  document.querySelectorAll("[data-toggle]").forEach((btn) => btn.addEventListener("click", async () => {
    const active = btn.dataset.active === "true";
    if (!await AdminUtils.showConfirm(`${active ? "Deactivate" : "Activate"} this user?`)) return;
    await AdminUtils.apiPatch(`/api/admin/settings/users/${btn.dataset.toggle}`, { is_active: !active });
    AdminUtils.showToast("User updated");
    loadUsers();
  }));
  document.querySelectorAll("[data-delete]").forEach((btn) => btn.addEventListener("click", async () => {
    if (!await AdminUtils.showConfirm("Delete this user?")) return;
    await AdminUtils.apiDelete(`/api/admin/settings/users/${btn.dataset.delete}`);
    AdminUtils.showToast("User deleted");
    loadUsers();
  }));
}

function openAddModal() {
  document.getElementById("userForm").reset();
  document.getElementById("userId").value = "";
  document.getElementById("userPasswordWrap").style.display = "";
  document.getElementById("userModalTitle").textContent = "Add User";
  new bootstrap.Modal(document.getElementById("userModal")).show();
}

async function openEditModal(id) {
  const data = await AdminUtils.apiGet(`/api/admin/settings/users/${id}`);
  const u = data.user;
  document.getElementById("userId").value = u.id;
  document.getElementById("userFullName").value = u.full_name;
  document.getElementById("userEmail").value = u.email;
  document.getElementById("userEmail").readOnly = true;
  document.getElementById("userUsername").value = u.username || "";
  document.getElementById("userRole").value = u.role_name || "User";
  document.getElementById("userActive").checked = u.is_active;
  document.getElementById("userPasswordWrap").style.display = "none";
  document.getElementById("userModalTitle").textContent = "Edit User";
  new bootstrap.Modal(document.getElementById("userModal")).show();
}

async function saveUser() {
  const form = document.getElementById("userForm");
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const id = document.getElementById("userId").value;
  const body = {
    full_name: document.getElementById("userFullName").value,
    username: document.getElementById("userUsername").value || null,
    role_name: document.getElementById("userRole").value,
    is_active: document.getElementById("userActive").checked,
  };
  try {
    if (id) {
      await AdminUtils.apiPut(`/api/admin/settings/users/${id}`, body);
    } else {
      await AdminUtils.apiPost("/api/admin/settings/users", {
        ...body,
        email: document.getElementById("userEmail").value,
        password: document.getElementById("userPassword").value,
      });
    }
    bootstrap.Modal.getInstance(document.getElementById("userModal"))?.hide();
    AdminUtils.showToast("User saved");
    loadUsers();
  } catch (e) {
    AdminUtils.showToast(e.message, "error");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const user = await AdminUtils.checkAdminAuth();
  if (!user) return;
  initAdminLayout("settings-users", "USER", [
    { label: "Dashboard", href: "/admin/dashboard.html" },
    { label: "Settings" },
    { label: "User" },
  ]);
  document.getElementById("adminPageActions").innerHTML = `<button class="btn-admin-primary" id="addUserBtn">+ Add User</button>`;
  mountPageTemplate();
  AdminUtils.renderTableControls(document.getElementById("tableControls"), usersLimit,
    (n) => { usersLimit = n; usersPage = 1; loadUsers(); },
    (q) => { usersSearch = q; usersPage = 1; loadUsers(); });
  document.getElementById("addUserBtn").addEventListener("click", openAddModal);
  document.getElementById("saveUserBtn").addEventListener("click", saveUser);
  await loadRolesDropdown();
  await loadUsers();
});

function mountPageTemplate() {
  const tpl = document.getElementById("pageTemplate");
  const target = document.getElementById("adminContent");
  if (tpl && target) target.appendChild(tpl.content.cloneNode(true));
}
