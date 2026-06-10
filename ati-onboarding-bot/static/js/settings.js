const PREFERENCE_KEYS = [
  "ati_theme",
  "ati_chat_density",
  "ati_send_on_enter",
  "ati_show_chips",
  "ati_show_typing",
  "ati_reduce_motion",
];

const SETTINGS = {
  theme: {
    key: "ati_theme",
    default: "system",
    parse: (v) => (["system", "light", "dark"].includes(v) ? v : "system"),
    apply(value) {
      if (typeof setTheme === "function") {
        setTheme(value);
      } else {
        document.documentElement.setAttribute("data-theme", value);
      }
    },
  },
  chatDensity: {
    key: "ati_chat_density",
    default: "comfortable",
    parse: (v) => (v === "compact" ? "compact" : "comfortable"),
    apply(value) {
      if (value === "compact") {
        document.documentElement.setAttribute("data-chat-density", "compact");
      } else {
        document.documentElement.removeAttribute("data-chat-density");
      }
    },
  },
  sendOnEnter: {
    key: "ati_send_on_enter",
    default: true,
    parse: (v) => v !== "false",
    apply() {},
  },
  showChips: {
    key: "ati_show_chips",
    default: true,
    parse: (v) => v !== "false",
    apply(value) {
      if (!value) {
        const area = document.getElementById("chips");
        if (area) area.innerHTML = "";
      }
    },
  },
  showTyping: {
    key: "ati_show_typing",
    default: true,
    parse: (v) => v !== "false",
    apply(value) {
      if (!value) {
        const el = document.getElementById("typing");
        if (el) el.classList.add("d-none");
      }
    },
  },
  reduceMotion: {
    key: "ati_reduce_motion",
    default: false,
    parse: (v) => v === "true",
    apply(value) {
      const prefersReduced =
        typeof window.matchMedia === "function" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (value || prefersReduced) {
        document.documentElement.setAttribute("data-reduce-motion", "true");
      } else {
        document.documentElement.removeAttribute("data-reduce-motion");
      }
    },
  },
};

function readRaw(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeRaw(key, value) {
  try {
    localStorage.setItem(key, String(value));
  } catch {
    /* ignore */
  }
}

function getSetting(name) {
  const def = SETTINGS[name];
  if (!def) return null;
  const raw = readRaw(def.key);
  if (raw === null) return def.default;
  return def.parse(raw);
}

function setSetting(name, value) {
  const def = SETTINGS[name];
  if (!def) return;
  const parsed = def.parse(String(value));
  writeRaw(def.key, parsed);
  def.apply(parsed);
  syncPanelControls();
}

function applyAllSettings() {
  Object.keys(SETTINGS).forEach((name) => {
    SETTINGS[name].apply(getSetting(name));
  });
}

function isChatPage() {
  return document.body?.dataset?.page === "chat";
}

function buildPanelHtml() {
  const showChat = isChatPage();
  return `
    <div id="settingsOverlay" class="settings-overlay d-none" aria-hidden="true">
      <div class="settings-backdrop" data-close-settings></div>
      <aside class="settings-drawer" role="dialog" aria-modal="true" aria-labelledby="settingsTitle" tabindex="-1">
        <header class="settings-header">
          <h2 id="settingsTitle">Settings</h2>
          <button type="button" class="settings-close" data-close-settings aria-label="Close settings">&times;</button>
        </header>
        <div class="settings-body">
          <section class="settings-section">
            <h3 class="settings-section-title">Appearance</h3>
            <div class="settings-row">
              <span class="settings-label">Theme</span>
              <div class="settings-segmented" data-setting="theme" role="group" aria-label="Theme">
                <button type="button" data-value="system">System</button>
                <button type="button" data-value="light">Light</button>
                <button type="button" data-value="dark">Dark</button>
              </div>
            </div>
            <div class="settings-row">
              <span class="settings-label">Chat text size</span>
              <div class="settings-segmented" data-setting="chatDensity" role="group" aria-label="Chat text size">
                <button type="button" data-value="comfortable">Comfortable</button>
                <button type="button" data-value="compact">Compact</button>
              </div>
            </div>
          </section>
          <section class="settings-section${showChat ? "" : " d-none"}" id="settingsChatSection">
            <h3 class="settings-section-title">Chat</h3>
            <div class="settings-row">
              <span class="settings-label">Send on Enter</span>
              <label class="settings-toggle">
                <input type="checkbox" data-setting="sendOnEnter">
                <span class="settings-toggle-track" aria-hidden="true"></span>
              </label>
            </div>
            <div class="settings-row">
              <span class="settings-label">Suggestion chips</span>
              <label class="settings-toggle">
                <input type="checkbox" data-setting="showChips">
                <span class="settings-toggle-track" aria-hidden="true"></span>
              </label>
            </div>
            <div class="settings-row">
              <span class="settings-label">Typing indicator</span>
              <label class="settings-toggle">
                <input type="checkbox" data-setting="showTyping">
                <span class="settings-toggle-track" aria-hidden="true"></span>
              </label>
            </div>
          </section>
          <section class="settings-section">
            <h3 class="settings-section-title">Accessibility</h3>
            <div class="settings-row">
              <span class="settings-label">Reduce motion</span>
              <label class="settings-toggle">
                <input type="checkbox" data-setting="reduceMotion">
                <span class="settings-toggle-track" aria-hidden="true"></span>
              </label>
            </div>
          </section>
          <div class="settings-actions">
            <button type="button" class="btn-secondary-custom settings-reset" id="settingsResetBtn">Reset all preferences</button>
          </div>
        </div>
      </aside>
    </div>
  `;
}

function syncSegmented(group, value) {
  group.querySelectorAll("button[data-value]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.value === String(value));
    btn.setAttribute("aria-pressed", btn.dataset.value === String(value) ? "true" : "false");
  });
}

function syncPanelControls() {
  const overlay = document.getElementById("settingsOverlay");
  if (!overlay) return;

  overlay.querySelectorAll(".settings-segmented[data-setting]").forEach((group) => {
    const name = group.dataset.setting;
    syncSegmented(group, getSetting(name));
  });

  overlay.querySelectorAll("input[data-setting]").forEach((input) => {
    const name = input.dataset.setting;
    input.checked = Boolean(getSetting(name));
  });
}

function bindPanelEvents() {
  const overlay = document.getElementById("settingsOverlay");
  if (!overlay || overlay.dataset.bound === "true") return;
  overlay.dataset.bound = "true";

  overlay.querySelectorAll("[data-close-settings]").forEach((el) => {
    el.addEventListener("click", closeSettingsPanel);
  });

  overlay.querySelectorAll(".settings-segmented[data-setting]").forEach((group) => {
    const name = group.dataset.setting;
    group.querySelectorAll("button[data-value]").forEach((btn) => {
      btn.addEventListener("click", () => setSetting(name, btn.dataset.value));
    });
  });

  overlay.querySelectorAll("input[data-setting]").forEach((input) => {
    const name = input.dataset.setting;
    input.addEventListener("change", () => setSetting(name, input.checked));
  });

  document.getElementById("settingsResetBtn")?.addEventListener("click", resetAllPreferences);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !overlay.classList.contains("d-none")) {
      closeSettingsPanel();
    }
  });
}

function openSettingsPanel() {
  const overlay = document.getElementById("settingsOverlay");
  if (!overlay) return;

  const chatSection = document.getElementById("settingsChatSection");
  if (chatSection) {
    chatSection.classList.toggle("d-none", !isChatPage());
  }

  syncPanelControls();
  overlay.classList.remove("d-none");
  overlay.setAttribute("aria-hidden", "false");
  document.body.classList.add("settings-open");
  overlay.querySelector(".settings-drawer")?.focus();
}

function closeSettingsPanel() {
  const overlay = document.getElementById("settingsOverlay");
  if (!overlay) return;
  overlay.classList.add("d-none");
  overlay.setAttribute("aria-hidden", "true");
  document.body.classList.remove("settings-open");
}

function resetAllPreferences() {
  PREFERENCE_KEYS.forEach((key) => {
    try {
      localStorage.removeItem(key);
    } catch {
      /* ignore */
    }
  });
  applyAllSettings();
  syncPanelControls();
  closeSettingsPanel();
}

function bindSettingsTriggers() {
  document.querySelectorAll("[data-open-settings]").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      openSettingsPanel();
    });
  });
}

function initSettingsPanel() {
  if (!document.getElementById("settingsOverlay")) {
    document.body.insertAdjacentHTML("beforeend", buildPanelHtml());
    bindPanelEvents();
  }
  applyAllSettings();
  bindSettingsTriggers();
}

document.addEventListener("DOMContentLoaded", initSettingsPanel);
