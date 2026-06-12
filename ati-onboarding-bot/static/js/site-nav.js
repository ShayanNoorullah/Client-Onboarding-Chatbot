const PUBLIC_NAV_STATIC = [
  { id: "about", label: "About", href: "/about.html" },
  { id: "contact", label: "Contact", href: "/contact.html" },
  { id: "privacy", label: "Privacy", href: "/privacy.html" },
];

function buildNavItems(user, compact) {
  const items = [];

  if (user) {
    const isAdmin = user.role === "admin";
    items.push({
      id: "home",
      label: isAdmin ? "Dashboard" : "Chat",
      href: isAdmin ? "/admin/dashboard.html" : "/chat.html",
    });
    items.push(...PUBLIC_NAV_STATIC);
    if (isAdmin) {
      items.push({ id: "chat", label: "Chat", href: "/chat.html" });
    }
    items.push({ id: "settings", label: "Settings", href: "#", settings: true });
    items.push({ id: "logout", label: "Log out", href: "#", logout: true });
  } else {
    items.push({ id: "home", label: "Home", href: "/login.html" });
    items.push(...PUBLIC_NAV_STATIC);
    items.push({ id: "settings", label: "Settings", href: "#", settings: true });
    if (!compact) {
      items.push({ id: "signin", label: "Sign in", href: "/login.html" });
    }
  }

  return items;
}

function renderSiteNav(mount, user, activePage, compact) {
  const items = buildNavItems(user, compact);
  const navLinks = items
    .map((item) => {
      const cls = item.id === activePage ? "active" : "";
      if (item.logout) {
        return `<a href="#" class="${cls}" data-logout="true">${item.label}</a>`;
      }
      if (item.settings) {
        return `<a href="#" class="${cls}" data-open-settings>${item.label}</a>`;
      }
      return `<a href="${item.href}" class="${cls}">${item.label}</a>`;
    })
    .join("");

  const brandHref = typeof homePathForUser === "function"
    ? homePathForUser(user)
    : (user ? (user.role === "admin" ? "/admin/dashboard.html" : "/chat.html") : "/login.html");

  mount.innerHTML = `
    <nav class="site-nav">
      <a href="${brandHref}" class="site-nav-brand">Client Onboarding Agent</a>
      <button type="button" class="site-nav-toggle" aria-label="Toggle menu" aria-expanded="false">
        <svg width="20" height="20" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5z"/></svg>
      </button>
      <div class="site-nav-links">${navLinks}</div>
    </nav>
  `;

  const nav = mount.querySelector(".site-nav");
  const toggle = mount.querySelector(".site-nav-toggle");
  toggle?.addEventListener("click", () => {
    const open = nav.classList.toggle("site-nav--open");
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  });

  mount.querySelectorAll("[data-open-settings]").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      if (typeof openSettingsPanel === "function") openSettingsPanel();
    });
  });

  mount.querySelector("[data-logout]")?.addEventListener("click", async (e) => {
    e.preventDefault();
    if (typeof logoutUser === "function") {
      await logoutUser();
    } else if (typeof API !== "undefined") {
      await API.post("/api/auth/logout", {});
    }
    window.location.replace("/login.html");
  });
}

async function resolveNavUser() {
  if (typeof readCachedAuthUser === "function") {
    const cached = readCachedAuthUser();
    if (cached) return cached;
  }
  if (typeof fetchAuthUser === "function") {
    return fetchAuthUser();
  }
  if (typeof getCurrentUserOptional === "function") {
    return getCurrentUserOptional();
  }
  try {
    const res = await fetch("/api/auth/me", { credentials: "include", headers: { Accept: "application/json" } });
    if (!res.ok) return null;
    const data = await res.json();
    return data.user || null;
  } catch {
    return null;
  }
}

async function initSiteNav() {
  const mount = document.getElementById("siteNav");
  if (!mount) return;

  const activePage = document.body.dataset.page || "";
  const compact = document.body.dataset.navCompact === "true";
  const isAuthPage = /\/(login|register)\.html$/i.test(window.location.pathname);

  if (!isAuthPage) {
    const cached = typeof readCachedAuthUser === "function" ? readCachedAuthUser() : null;
    if (cached) {
      renderSiteNav(mount, cached, activePage, compact);
    }
  }

  const user = typeof fetchSessionUser === "function"
    ? await fetchSessionUser()
    : await resolveNavUser();
  renderSiteNav(mount, user, activePage, compact);
}

document.addEventListener("DOMContentLoaded", initSiteNav);
