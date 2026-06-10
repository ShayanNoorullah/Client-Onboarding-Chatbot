const THEME_KEY = "ati_theme";
const VALID_THEMES = ["system", "light", "dark"];

function getTheme() {
  try {
    const stored = localStorage.getItem(THEME_KEY);
    return VALID_THEMES.includes(stored) ? stored : "system";
  } catch {
    return "system";
  }
}

function applyTheme(mode) {
  const theme = VALID_THEMES.includes(mode) ? mode : "system";
  document.documentElement.setAttribute("data-theme", theme);
}

function setTheme(mode) {
  const theme = VALID_THEMES.includes(mode) ? mode : "system";
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* ignore */
  }
  applyTheme(theme);
}

function initTheme() {
  applyTheme(getTheme());
  if (typeof window.matchMedia !== "function") return;

  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  const handler = () => {
    if (getTheme() === "system") applyTheme("system");
  };
  if (mq.addEventListener) {
    mq.addEventListener("change", handler);
  } else if (mq.addListener) {
    mq.addListener(handler);
  }
}

document.addEventListener("DOMContentLoaded", initTheme);
