const ADMIN_NAV = [
  { id: "dashboard", label: "Dashboard", href: "/admin/dashboard.html" },
  { id: "users", label: "Users", href: "/admin/users.html" },
  { id: "briefs", label: "Briefs", href: "/admin/briefs.html" },
  { id: "sessions", label: "Chats", href: "/admin/sessions.html" },
  { id: "api-docs", label: "API Docs", href: "/docs", external: true },
  { id: "health", label: "Health Check", href: "/admin/health.html" },
  { id: "chat", label: "Chat", href: "/chat.html" },
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
  const sidebar = document.getElementById("adminSidebar");
  if (!sidebar) return;
  if (sidebar.classList.contains("admin-sidebar-drawer-open")) {
    closeAdminSidebar();
  } else {
    openAdminSidebar();
  }
}

function initAdminLayout(activeId, pageTitle) {
  const root = document.getElementById("adminRoot");
  if (!root) return;

  if (!document.getElementById("adminSidebarBackdrop")) {
    const backdrop = document.createElement("div");
    backdrop.id = "adminSidebarBackdrop";
    backdrop.className = "admin-sidebar-backdrop";
    backdrop.addEventListener("click", closeAdminSidebar);
    document.body.prepend(backdrop);
  }

  const navHtml = ADMIN_NAV.map((item) => {
    const cls = item.id === activeId ? "active" : "";
    const ext = item.external ? " external" : "";
    const target = item.external ? ' target="_blank" rel="noopener"' : "";
    return `<a href="${item.href}" class="${cls}${ext}"${target}>${item.label}</a>`;
  }).join("");

  root.innerHTML = `
    <aside class="admin-sidebar" id="adminSidebar">
      <div class="admin-sidebar-brand">ATI Admin</div>
      <div class="admin-sidebar-sub">Awesome Technologies Inc.</div>
      <nav class="admin-nav">${navHtml}</nav>
      <div class="admin-sidebar-footer">
        <button type="button" data-open-settings>Settings</button>
        <a href="/about.html" class="footer-link">About</a>
        <a href="/contact.html" class="footer-link">Contact</a>
        <a href="/privacy.html" class="footer-link">Privacy</a>
        <button type="button" id="logoutBtn">Log out</button>
      </div>
    </aside>
    <main class="admin-main">
      <div class="admin-topbar">
        <button type="button" id="adminSidebarToggle" class="admin-sidebar-toggle" aria-label="Open menu">
          <svg width="20" height="20" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5z"/></svg>
        </button>
        ${pageTitle ? `<h1>${pageTitle}</h1>` : ""}
      </div>
      <div id="adminContent"></div>
    </main>
  `;

  document.getElementById("adminSidebarToggle")?.addEventListener("click", toggleAdminSidebar);
  root.querySelectorAll(".admin-nav a:not(.external)").forEach((link) => {
    link.addEventListener("click", closeAdminSidebar);
  });

  root.querySelectorAll("[data-open-settings]").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      if (typeof openSettingsPanel === "function") openSettingsPanel();
    });
  });

  document.getElementById("logoutBtn")?.addEventListener("click", async () => {
    if (typeof logoutUser === "function") {
      await logoutUser();
    } else {
      await API.post("/api/auth/logout", {});
    }
    window.location.href = "/login.html";
  });
}

async function requireAdmin() {
  const user = await requireAuth("/login.html");
  if (!user || user.role !== "admin") {
    window.location.href = "/chat.html";
    return null;
  }
  if (typeof cacheAuthUser === "function") {
    cacheAuthUser(user);
  }
  return user;
}
