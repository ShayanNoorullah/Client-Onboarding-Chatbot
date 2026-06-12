(function () {
  const STORAGE_KEY = "coa_sidebar_mode";

  function getMode() {
    return localStorage.getItem(STORAGE_KEY) === "rail" ? "rail" : "expanded";
  }

  function isRail() {
    return getMode() === "rail";
  }

  function isMobile() {
    return window.innerWidth <= 768;
  }

  function syncToggleUi() {
    const rail = isRail();
    const mobile = isMobile();
    document.querySelectorAll("[data-sidebar-rail-toggle]").forEach((btn) => {
      btn.setAttribute("aria-pressed", rail ? "true" : "false");
      btn.title = rail ? "Expand sidebar" : "Collapse sidebar";
    });
    const topToggle = document.getElementById("adminSidebarToggle");
    const topIcon = document.getElementById("adminSidebarToggleIcon");
    if (topToggle && topIcon) {
      topToggle.title = mobile ? (rail ? "Close menu" : "Open menu") : (rail ? "Expand sidebar" : "Collapse sidebar");
      topIcon.className = mobile ? "fa fa-bars" : (rail ? "fa fa-angles-right" : "fa fa-angles-left");
    }
  }

  function applyMode(mode) {
    const rail = mode === "rail";
    document.body.classList.toggle("sidebar-rail", rail && !isMobile());
    syncToggleUi();
  }

  function toggleRail() {
    const next = isRail() ? "expanded" : "rail";
    localStorage.setItem(STORAGE_KEY, next);
    applyMode(next);
    return next;
  }

  function initSidebarRail() {
    applyMode(getMode());
    document.querySelectorAll("[data-sidebar-rail-toggle]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        toggleRail();
      });
    });
    window.addEventListener("resize", () => applyMode(getMode()));
  }

  window.SidebarRail = { initSidebarRail, toggleRail, isRail, getMode, syncToggleUi };
})();
