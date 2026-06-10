const ADMIN_NAV = [
  { id: "dashboard", label: "Dashboard", href: "/admin/dashboard.html" },
  { id: "users", label: "Users", href: "/admin/users.html" },
  { id: "briefs", label: "Briefs", href: "/admin/briefs.html" },
  { id: "sessions", label: "Chats", href: "/admin/sessions.html" },
  { id: "api-docs", label: "API Docs", href: "/docs", external: true },
  { id: "health", label: "Health Check", href: "/admin/health.html" },
  { id: "chat", label: "Chat", href: "/chat.html" },
];

function initAdminLayout(activeId, pageTitle) {
  const root = document.getElementById("adminRoot");
  if (!root) return;

  const navHtml = ADMIN_NAV.map((item) => {
    const cls = item.id === activeId ? "active" : "";
    const ext = item.external ? " external" : "";
    const target = item.external ? ' target="_blank" rel="noopener"' : "";
    return `<a href="${item.href}" class="${cls}${ext}"${target}>${item.label}</a>`;
  }).join("");

  root.innerHTML = `
    <aside class="admin-sidebar">
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
      ${pageTitle ? `<h1>${pageTitle}</h1>` : ""}
      <div id="adminContent"></div>
    </main>
  `;

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
