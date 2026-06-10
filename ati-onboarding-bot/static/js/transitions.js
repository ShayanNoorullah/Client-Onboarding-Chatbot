function uiAnimationsEnabled() {
  if (typeof getSetting === "function") {
    if (getSetting("reduceMotion")) return false;
    return getSetting("uiAnimations") !== false;
  }
  if (document.documentElement.dataset.reduceMotion === "true") return false;
  return document.documentElement.dataset.uiAnimations !== "false";
}

function applyUiAnimationsAttribute() {
  const enabled = uiAnimationsEnabled();
  if (enabled) {
    document.documentElement.setAttribute("data-ui-animations", "true");
  } else {
    document.documentElement.setAttribute("data-ui-animations", "false");
  }
}

function animateMessageRow(row) {
  if (!row || !uiAnimationsEnabled()) return;
  row.classList.add("msg-enter");
  row.addEventListener("animationend", () => row.classList.remove("msg-enter"), { once: true });
}

function initPageTransitions() {
  applyUiAnimationsAttribute();
  if (uiAnimationsEnabled()) {
    document.body.classList.add("page-enter");
    document.body.addEventListener("animationend", () => {
      document.body.classList.remove("page-enter");
    }, { once: true });
  }

  document.addEventListener("click", (e) => {
    const link = e.target.closest("a[href]");
    if (!link || !uiAnimationsEnabled()) return;
    if (link.target === "_blank" || link.hasAttribute("download")) return;
    if (link.getAttribute("href")?.startsWith("#")) return;
    if (link.hasAttribute("data-open-settings") || link.hasAttribute("data-logout")) return;
    const href = link.getAttribute("href");
    if (!href || href.startsWith("javascript:")) return;
    try {
      const dest = new URL(href, window.location.origin);
      if (dest.origin !== window.location.origin) return;
    } catch {
      return;
    }
    e.preventDefault();
    document.body.classList.add("page-exit");
    setTimeout(() => { window.location.href = href; }, 120);
  });
}

document.addEventListener("DOMContentLoaded", initPageTransitions);
