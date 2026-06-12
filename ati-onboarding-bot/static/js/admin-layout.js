const ADMIN_NAV = [
  { id: "dashboard", label: "Dashboard", href: "/admin/dashboard.html", icon: "fa-th-large" },
  {
    id: "pipeline", label: "Pipeline", icon: "fa-circle-nodes", children: [
      { id: "sessions", label: "Onboarding Sessions", href: "/admin/sessions.html", icon: "fa-comments" },
      { id: "briefs", label: "Briefs", href: "/admin/briefs.html", icon: "fa-file-lines" },
      { id: "pipeline-types", label: "Project Types", href: "/admin/pipeline-types.html", icon: "fa-diagram-project" },
    ],
  },
  {
    id: "configuration", label: "Configuration", icon: "fa-sliders", children: [
      { id: "config-ai", label: "AI Configuration", href: "/admin/config-ai.html", icon: "fa-robot" },
      { id: "config-system", label: "System Configuration", href: "/admin/config-system.html", icon: "fa-server" },
      { id: "config-smtp", label: "SMTP", href: "/admin/config-smtp.html", icon: "fa-envelope" },
      { id: "config-email", label: "Email Templates", href: "/admin/config-email-templates.html", icon: "fa-envelope-open-text" },
      { id: "config-followup", label: "Follow-up Timing", href: "/admin/config-followup.html", icon: "fa-clock" },
      { id: "config-tenant", label: "Workspace", href: "/admin/config-tenant.html", icon: "fa-building" },
      { id: "config-api-keys", label: "API Keys", href: "/admin/config-api-keys.html", icon: "fa-key" },
      { id: "config-usage", label: "Usage & Limits", href: "/admin/config-usage.html", icon: "fa-chart-pie" },
      { id: "config-webhooks", label: "Webhooks", href: "/admin/config-webhooks.html", icon: "fa-plug" },
      { id: "config-integrations", label: "Integrations", href: "/admin/config-integrations.html", icon: "fa-puzzle-piece" },
      { id: "config-learning", label: "Learning", href: "/admin/learning.html", icon: "fa-brain" },
    ],
  },
  {
    id: "settings", label: "Settings", icon: "fa-cog", children: [
      { id: "settings-actions", label: "Application Action", href: "/admin/settings-actions.html", icon: "fa-bolt" },
      { id: "settings-modules", label: "Application Module", href: "/admin/settings-modules.html", icon: "fa-cubes" },
      { id: "settings-pages", label: "Application Page", href: "/admin/settings-pages.html", icon: "fa-file" },
      { id: "settings-roles", label: "Role", href: "/admin/settings-roles.html", icon: "fa-user-shield" },
      { id: "settings-users", label: "User", href: "/admin/settings-users.html", icon: "fa-users" },
      { id: "settings-audit", label: "Audit Log", href: "/admin/settings-audit.html", icon: "fa-clipboard-list" },
    ],
  },
  { id: "reports", label: "Reports", href: "/admin/reports.html", icon: "fa-chart-bar" },
];

function closeAdminSidebar() {
  document.getElementById("adminSidebar")?.classList.remove("admin-sidebar-drawer-open");
  document.getElementById("adminSidebarBackdrop")?.classList.remove("admin-sidebar-backdrop--visible");
}

function openAdminSidebar() {
  document.getElementById("adminSidebar")?.classList.add("admin-sidebar-drawer-open");
  document.getElementById("adminSidebarBackdrop")?.classList.add("admin-sidebar-backdrop--visible");
}

function toggleAdminSidebar() {
  if (window.innerWidth <= 768) {
    const sidebar = document.getElementById("adminSidebar");
    if (!sidebar) return;
    if (sidebar.classList.contains("admin-sidebar-drawer-open")) closeAdminSidebar();
    else openAdminSidebar();
    if (typeof SidebarRail !== "undefined") SidebarRail.syncToggleUi();
  } else if (typeof SidebarRail !== "undefined") {
    SidebarRail.toggleRail();
  }
}

function _findParentGroup(activeId) {
  for (const item of ADMIN_NAV) {
    if (item.id === activeId) return null;
    if (item.children) {
      for (const child of item.children) {
        if (child.id === activeId) return item.id;
      }
    }
  }
  return null;
}

function _navLink(item, activeId) {
  const cls = item.id === activeId ? "admin-nav-item active" : "admin-nav-item";
  const icon = item.icon ? `<i class="fa ${item.icon} me-2"></i>` : "";
  return `<a href="${item.href}" class="${cls}" title="${item.label}">${icon}<span class="nav-label">${item.label}</span></a>`;
}

function _buildNavHtml(activeId) {
  const parentGroup = _findParentGroup(activeId);
  return ADMIN_NAV.map((item) => {
    if (item.children) {
      const isOpen = item.id === parentGroup;
      const sub = item.children.map((c) => _navLink(c, activeId)).join("");
      return `<div class="admin-nav-group${isOpen ? " open" : ""}" data-group="${item.id}">
        <button type="button" class="admin-nav-group-toggle" data-toggle-group title="${item.label}">
          <span><i class="fa ${item.icon} me-2 icon-only"></i><span class="nav-label">${item.label}</span></span>
          <span class="chevron">&#9656;</span>
        </button>
        <div class="admin-nav-sub">${sub}</div>
      </div>`;
    }
    return _navLink(item, activeId);
  }).join("");
}

function _buildBreadcrumb(breadcrumbs) {
  if (!breadcrumbs || !breadcrumbs.length) return "";
  const parts = breadcrumbs.map((b, i) => {
    if (i === breadcrumbs.length - 1) return `<strong>${b.label || b}</strong>`;
    if (b.href) return `<a href="${b.href}">${b.label || b}</a>`;
    return `<span>${b.label || b}</span>`;
  });
  return `<nav class="admin-breadcrumb">${parts.join("<span>/</span>")}</nav>`;
}

function initAdminLayout(activeId, pageTitle, breadcrumbs) {
  const root = document.getElementById("adminRoot");
  if (!root) return;

  if (!document.getElementById("adminSidebarBackdrop")) {
    const backdrop = document.createElement("div");
    backdrop.id = "adminSidebarBackdrop";
    backdrop.className = "admin-sidebar-backdrop";
    backdrop.addEventListener("click", closeAdminSidebar);
    document.body.prepend(backdrop);
  }

  const navHtml = _buildNavHtml(activeId);
  const breadcrumbHtml = _buildBreadcrumb(breadcrumbs);

  root.innerHTML = `
    <header class="admin-topnav">
      <button type="button" id="adminSidebarToggle" class="admin-sidebar-toggle" aria-label="Toggle sidebar" title="Collapse sidebar">
        <i class="fa fa-angles-left" id="adminSidebarToggleIcon"></i>
      </button>
      <a href="/admin/dashboard.html" class="admin-topnav-brand">Client Onboarding Agent</a>
      <form class="admin-topnav-search" id="adminSearchForm">
        <input type="search" placeholder="Search..." id="adminSearchInput">
      </form>
      <select id="adminTenantSelect" class="admin-tenant-select d-none" title="Switch tenant" aria-label="Switch tenant"></select>
      <div class="admin-topnav-user">
        <button type="button" class="admin-topnav-user-btn" id="adminUserBtn">
          <span id="adminUserName">Admin</span> &#9662;
        </button>
        <div class="admin-topnav-dropdown" id="adminUserDropdown">
          <a href="/admin/settings-users.html">Account</a>
          <button type="button" id="logoutBtnTop">Logout</button>
        </div>
      </div>
    </header>
    <div class="admin-body-wrap">
      <aside class="admin-sidebar" id="adminSidebar">
        <div class="admin-sidebar-header">
          <div class="admin-sidebar-brand">Admin</div>
          <button type="button" class="admin-sidebar-rail-btn" data-sidebar-rail-toggle aria-label="Toggle sidebar width" title="Collapse sidebar">
            <i class="fa fa-angles-left"></i>
          </button>
        </div>
        <nav class="admin-nav">${navHtml}</nav>
        <div class="admin-sidebar-footer">
          <a href="/admin/health.html" class="admin-footer-link" title="Health Check"><i class="fa fa-heart-pulse"></i><span class="footer-label">Health Check</span></a>
          <a href="/docs" target="_blank" rel="noopener" class="admin-footer-link" title="API Docs"><i class="fa fa-book"></i><span class="footer-label">API Docs</span></a>
          <button type="button" class="admin-footer-link" data-open-settings title="Theme Settings"><i class="fa fa-palette"></i><span class="footer-label">Theme Settings</span></button>
          <button type="button" class="admin-footer-link" id="logoutBtn" title="Log out"><i class="fa fa-right-from-bracket"></i><span class="footer-label">Log out</span></button>
        </div>
      </aside>
      <main class="admin-main">
        ${breadcrumbHtml}
        <div class="admin-page-header">
          <h1>${pageTitle || ""}</h1>
          <div id="adminPageActions"></div>
        </div>
        <div id="adminContent"></div>
      </main>
    </div>
  `;

  document.getElementById("adminSidebarToggle")?.addEventListener("click", toggleAdminSidebar);
  root.querySelectorAll(".admin-nav a").forEach((link) => {
    link.addEventListener("click", closeAdminSidebar);
  });
  root.querySelectorAll("[data-toggle-group]").forEach((btn) => {
    btn.addEventListener("click", () => {
      btn.closest(".admin-nav-group")?.classList.toggle("open");
    });
  });

  document.getElementById("adminSearchForm")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = document.getElementById("adminSearchInput")?.value?.trim();
    if (q) window.location.href = `/admin/dashboard.html?search=${encodeURIComponent(q)}`;
  });

  const userBtn = document.getElementById("adminUserBtn");
  const dropdown = document.getElementById("adminUserDropdown");
  userBtn?.addEventListener("click", () => dropdown?.classList.toggle("show"));
  document.addEventListener("click", (e) => {
    if (!userBtn?.contains(e.target) && !dropdown?.contains(e.target)) {
      dropdown?.classList.remove("show");
    }
  });

  async function doLogout() {
    if (typeof logoutUser === "function") await logoutUser();
    else await API.post("/api/auth/logout", {});
    window.location.replace("/login.html");
  }
  document.getElementById("logoutBtn")?.addEventListener("click", doLogout);
  document.getElementById("logoutBtnTop")?.addEventListener("click", doLogout);

  root.querySelectorAll("[data-open-settings]").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      if (typeof openSettingsPanel === "function") openSettingsPanel();
    });
  });

  if (typeof SidebarRail !== "undefined") SidebarRail.initSidebarRail();

  if (typeof fetchSessionUser === "function") {
    fetchSessionUser().then(async (user) => {
      const el = document.getElementById("adminUserName");
      if (el && user) el.textContent = user.full_name || "Admin";
      const tenantSel = document.getElementById("adminTenantSelect");
      if (tenantSel && user?.is_super_admin) {
        try {
          const data = await AdminUtils.apiGet("/api/admin/tenants");
          const tenants = data.tenants || [];
          const current = AdminUtils.getTenantHeader() || user.tenant_id || "default";
          tenantSel.innerHTML = tenants.map((t) =>
            `<option value="${t.slug}" ${t.slug === current ? "selected" : ""}>${t.name}</option>`
          ).join("");
          tenantSel.classList.remove("d-none");
          tenantSel.addEventListener("change", () => {
            AdminUtils.setTenantHeader(tenantSel.value);
            window.location.reload();
          });
        } catch (_) { /* non-super-admin or API unavailable */ }
      }
    }).catch(() => {});
  }

  if (typeof initSettingsPanel === "function") initSettingsPanel();
}

async function requireAdmin() {
  const user = await requireAuth("/login.html");
  if (!user || user.role !== "admin") {
    window.location.replace("/chat.html");
    return null;
  }
  if (typeof cacheAuthUser === "function") cacheAuthUser(user);
  return user;
}
