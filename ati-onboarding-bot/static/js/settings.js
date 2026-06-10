const PREFERENCE_KEYS = [
  "ati_theme",
  "ati_theme_preset",
  "ati_custom_theme",
  "ati_chat_density",
  "ati_chat_width",
  "ati_chat_style",
  "ati_chat_user_bubble",
  "ati_chat_assistant_bubble",
  "ati_chat_accent",
  "ati_send_on_enter",
  "ati_show_chips",
  "ati_show_typing",
  "ati_auto_scroll",
  "ati_reduce_motion",
  "ati_ui_animations",
];

const THEME_PRESETS = [
  { id: "default", label: "Default", color: "#0D0D0D" },
  { id: "ocean", label: "Ocean", color: "#0369A1" },
  { id: "forest", label: "Forest", color: "#166534" },
  { id: "sunset", label: "Sunset", color: "#C2410C" },
  { id: "violet", label: "Violet", color: "#6D28D9" },
  { id: "slate", label: "Slate", color: "#334155" },
  { id: "high-contrast", label: "High contrast", color: "#000000" },
  { id: "custom", label: "Custom", color: "linear-gradient(135deg,#667eea,#764ba2)" },
];

const CUSTOM_THEME_DEFAULTS = {
  primary: "#0D0D0D",
  surface: "#FFFFFF",
  text: "#0D0D0D",
  accent: "#6B7280",
  border: "#E5E7EB",
};

let prefsSaveTimer = null;

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

function getCustomTheme() {
  try {
    const raw = readRaw("ati_custom_theme");
    if (!raw || raw === "{}") return { ...CUSTOM_THEME_DEFAULTS };
    return { ...CUSTOM_THEME_DEFAULTS, ...JSON.parse(raw) };
  } catch {
    return { ...CUSTOM_THEME_DEFAULTS };
  }
}

function setCustomTheme(colors) {
  writeRaw("ati_custom_theme", JSON.stringify(colors));
  applyCustomTheme(colors);
}

function applyCustomTheme(colors) {
  const root = document.documentElement.style;
  if (colors.primary) root.setProperty("--custom-primary", colors.primary);
  if (colors.surface) root.setProperty("--custom-surface", colors.surface);
  if (colors.text) root.setProperty("--custom-text", colors.text);
  if (colors.accent) root.setProperty("--custom-accent", colors.accent);
  if (colors.border) root.setProperty("--custom-border", colors.border);
  root.setProperty("--custom-muted", colors.surface || colors.primary || CUSTOM_THEME_DEFAULTS.surface);
  root.setProperty(
    "--custom-on-primary",
    (colors.text || "").toLowerCase() === "#ffffff" ? "#000000" : "#FFFFFF"
  );
}

function clearCustomThemeVars() {
  ["--custom-primary", "--custom-surface", "--custom-text", "--custom-accent", "--custom-border", "--custom-muted", "--custom-on-primary"].forEach((v) => {
    document.documentElement.style.removeProperty(v);
  });
}

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
  themePreset: {
    key: "ati_theme_preset",
    default: "default",
    parse: (v) => (THEME_PRESETS.some((p) => p.id === v) ? v : "default"),
    apply(value) {
      document.documentElement.setAttribute("data-theme-preset", value);
      if (value === "custom") {
        applyCustomTheme(getCustomTheme());
      } else {
        clearCustomThemeVars();
      }
      const panel = document.getElementById("customThemePanel");
      if (panel) panel.classList.toggle("d-none", value !== "custom");
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
  chatWidth: {
    key: "ati_chat_width",
    default: "wide",
    parse: (v) => (["narrow", "standard", "wide", "full"].includes(v) ? v : "wide"),
    apply(value) {
      document.documentElement.setAttribute("data-chat-width", value);
    },
  },
  chatStyle: {
    key: "ati_chat_style",
    default: "default",
    parse: (v) => (["default", "soft", "contrast", "minimal"].includes(v) ? v : "default"),
    apply(value) {
      if (value === "default") {
        document.documentElement.removeAttribute("data-chat-style");
      } else {
        document.documentElement.setAttribute("data-chat-style", value);
      }
    },
  },
  chatUserBubble: {
    key: "ati_chat_user_bubble",
    default: "",
    parse: (v) => (v && /^#[0-9A-Fa-f]{6}$/.test(v) ? v : ""),
    apply(value) {
      if (value) {
        document.documentElement.style.setProperty("--chat-user-bg", value);
      } else {
        document.documentElement.style.removeProperty("--chat-user-bg");
      }
    },
  },
  chatAssistantBubble: {
    key: "ati_chat_assistant_bubble",
    default: "",
    parse: (v) => (v && /^#[0-9A-Fa-f]{6}$/.test(v) ? v : ""),
    apply(value) {
      if (value) {
        document.documentElement.style.setProperty("--chat-assistant-bg", value);
      } else {
        document.documentElement.style.removeProperty("--chat-assistant-bg");
      }
    },
  },
  chatAccent: {
    key: "ati_chat_accent",
    default: "",
    parse: (v) => (v && /^#[0-9A-Fa-f]{6}$/.test(v) ? v : ""),
    apply(value) {
      if (value) {
        document.documentElement.style.setProperty("--chat-accent", value);
      } else {
        document.documentElement.style.removeProperty("--chat-accent");
      }
    },
  },
  sendOnEnter: {
    key: "ati_send_on_enter",
    default: true,
    parse: (v) => v !== "false" && v !== false,
    serialize: (v) => (v ? "true" : "false"),
    apply() {},
  },
  showChips: {
    key: "ati_show_chips",
    default: true,
    parse: (v) => v !== "false" && v !== false,
    serialize: (v) => (v ? "true" : "false"),
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
    parse: (v) => v !== "false" && v !== false,
    serialize: (v) => (v ? "true" : "false"),
    apply(value) {
      if (!value) {
        const el = document.getElementById("typing");
        if (el) el.classList.add("d-none");
      }
    },
  },
  autoScroll: {
    key: "ati_auto_scroll",
    default: true,
    parse: (v) => v !== "false" && v !== false,
    serialize: (v) => (v ? "true" : "false"),
    apply() {},
  },
  reduceMotion: {
    key: "ati_reduce_motion",
    default: false,
    parse: (v) => v === "true" || v === true,
    serialize: (v) => (v ? "true" : "false"),
    apply(value) {
      const prefersReduced =
        typeof window.matchMedia === "function" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (value || prefersReduced) {
        document.documentElement.setAttribute("data-reduce-motion", "true");
      } else {
        document.documentElement.removeAttribute("data-reduce-motion");
      }
      if (typeof applyUiAnimationsAttribute === "function") {
        applyUiAnimationsAttribute();
      }
    },
  },
  uiAnimations: {
    key: "ati_ui_animations",
    default: true,
    parse: (v) => v !== "false" && v !== false,
    serialize: (v) => (v ? "true" : "false"),
    apply() {
      if (typeof applyUiAnimationsAttribute === "function") {
        applyUiAnimationsAttribute();
      }
    },
  },
};

function getSetting(name) {
  const def = SETTINGS[name];
  if (!def) return null;
  const raw = readRaw(def.key);
  if (raw === null) return def.default;
  return def.parse(raw);
}

function serializeSetting(name, value) {
  const def = SETTINGS[name];
  if (!def) return String(value);
  if (def.serialize) return def.serialize(value);
  return String(value);
}

function setSetting(name, value, options = {}) {
  const def = SETTINGS[name];
  if (!def) return;
  const parsed = def.parse(value);
  writeRaw(def.key, serializeSetting(name, parsed));
  def.apply(parsed);
  syncPanelControls();
  if (!options.skipSave) schedulePreferencesSave();
}

function applyAllSettings() {
  Object.keys(SETTINGS).forEach((name) => {
    SETTINGS[name].apply(getSetting(name));
  });
  if (typeof applyUiAnimationsAttribute === "function") {
    applyUiAnimationsAttribute();
  }
}

function isAuthenticated() {
  return typeof readCachedAuthUser === "function" && Boolean(readCachedAuthUser()?.id);
}

function schedulePreferencesSave() {
  if (!isAuthenticated() || typeof API === "undefined") return;
  clearTimeout(prefsSaveTimer);
  prefsSaveTimer = setTimeout(() => {
    saveUserPreferences().catch(() => {});
  }, 300);
}

async function saveUserPreferences() {
  if (!isAuthenticated()) return;
  const payload = {};
  PREFERENCE_KEYS.forEach((key) => {
    payload[key] = readRaw(key) ?? "";
  });
  await API.put("/api/user/preferences", payload);
}

async function loadUserPreferences() {
  if (!isAuthenticated() || typeof API === "undefined") return false;
  try {
    const data = await API.get("/api/user/preferences");
    const prefs = data.preferences || {};
    Object.entries(prefs).forEach(([key, value]) => {
      if (PREFERENCE_KEYS.includes(key) && value != null) {
        writeRaw(key, String(value));
      }
    });
    applyAllSettings();
    syncPanelControls();
    return true;
  } catch {
    return false;
  }
}

function isChatPage() {
  return document.body?.dataset?.page === "chat";
}

function buildPresetSwatchesHtml() {
  return THEME_PRESETS.map(
    (p) => `<button type="button" class="theme-preset-swatch" data-preset="${p.id}" title="${p.label}" aria-label="${p.label}" style="--swatch-color:${p.color}"></button>`
  ).join("");
}

function buildCustomThemeHtml() {
  const c = getCustomTheme();
  const fields = [
    { key: "primary", label: "Primary" },
    { key: "surface", label: "Surface" },
    { key: "text", label: "Text" },
    { key: "accent", label: "Accent" },
    { key: "border", label: "Border" },
  ];
  return fields
    .map(
      (f) => `
    <div class="settings-color-row">
      <label for="custom_${f.key}">${f.label}</label>
      <input type="color" id="custom_${f.key}" data-custom-key="${f.key}" value="${c[f.key]}">
    </div>`
    )
    .join("");
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
              <span class="settings-label">Mode</span>
              <div class="settings-segmented" data-setting="theme" role="group" aria-label="Theme mode">
                <button type="button" data-value="system">System</button>
                <button type="button" data-value="light">Light</button>
                <button type="button" data-value="dark">Dark</button>
              </div>
            </div>
            <div class="settings-row settings-row-stack">
              <span class="settings-label">Color theme</span>
              <div class="theme-preset-grid" id="themePresetGrid">${buildPresetSwatchesHtml()}</div>
            </div>
            <div id="customThemePanel" class="custom-theme-panel d-none">
              <p class="settings-hint">Customize colors for your theme.</p>
              ${buildCustomThemeHtml()}
              <button type="button" class="btn-secondary-custom settings-reset-custom" id="resetCustomThemeBtn">Reset custom colors</button>
            </div>
            <div class="settings-row">
              <span class="settings-label">Chat text size</span>
              <div class="settings-segmented" data-setting="chatDensity" role="group" aria-label="Chat text size">
                <button type="button" data-value="comfortable">Comfortable</button>
                <button type="button" data-value="compact">Compact</button>
              </div>
            </div>
            <div class="settings-row settings-row-stack">
              <span class="settings-label">Chat width</span>
              <div class="settings-segmented settings-segmented--wrap" data-setting="chatWidth" role="group" aria-label="Chat width">
                <button type="button" data-value="narrow">Narrow</button>
                <button type="button" data-value="standard">Standard</button>
                <button type="button" data-value="wide">Wide</button>
                <button type="button" data-value="full">Full</button>
              </div>
            </div>
          </section>
          <section class="settings-section${showChat ? "" : " d-none"}" id="settingsChatSection">
            <h3 class="settings-section-title">Chat appearance</h3>
            <div class="settings-row settings-row-stack">
              <span class="settings-label">Bubble style</span>
              <div class="settings-segmented settings-segmented--wrap" data-setting="chatStyle" role="group" aria-label="Chat bubble style">
                <button type="button" data-value="default">Default</button>
                <button type="button" data-value="soft">Soft</button>
                <button type="button" data-value="contrast">Contrast</button>
                <button type="button" data-value="minimal">Minimal</button>
              </div>
            </div>
            <div class="settings-color-row">
              <label for="chatUserBubble">User bubble</label>
              <input type="color" id="chatUserBubble" data-chat-color="chatUserBubble" value="${getSetting("chatUserBubble") || "#F3F4F6"}">
              <button type="button" class="settings-color-clear" data-clear-color="chatUserBubble">Clear</button>
            </div>
            <div class="settings-color-row">
              <label for="chatAssistantBubble">Assistant bubble</label>
              <input type="color" id="chatAssistantBubble" data-chat-color="chatAssistantBubble" value="${getSetting("chatAssistantBubble") || "#FFFFFF"}">
              <button type="button" class="settings-color-clear" data-clear-color="chatAssistantBubble">Clear</button>
            </div>
            <div class="settings-color-row">
              <label for="chatAccentColor">Chat accent</label>
              <input type="color" id="chatAccentColor" data-chat-color="chatAccent" value="${getSetting("chatAccent") || "#0D0D0D"}">
              <button type="button" class="settings-color-clear" data-clear-color="chatAccent">Clear</button>
            </div>
          </section>
          <section class="settings-section${showChat ? "" : " d-none"}" id="settingsChatBehaviorSection">
            <h3 class="settings-section-title">Chat behavior</h3>
            <div class="settings-row">
              <span class="settings-label">Auto-scroll to new messages</span>
              <label class="settings-toggle">
                <input type="checkbox" data-setting="autoScroll">
                <span class="settings-toggle-track" aria-hidden="true"></span>
              </label>
            </div>
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
              <span class="settings-label">Thinking indicator</span>
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
            <div class="settings-row">
              <span class="settings-label">Interface animations</span>
              <label class="settings-toggle">
                <input type="checkbox" data-setting="uiAnimations">
                <span class="settings-toggle-track" aria-hidden="true"></span>
              </label>
            </div>
            <p class="settings-hint">Animations are off when Reduce motion is enabled.</p>
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

  const preset = getSetting("themePreset");
  overlay.querySelectorAll(".theme-preset-swatch").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.preset === preset);
    btn.setAttribute("aria-pressed", btn.dataset.preset === preset ? "true" : "false");
  });

  const customPanel = document.getElementById("customThemePanel");
  if (customPanel) customPanel.classList.toggle("d-none", preset !== "custom");
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

  overlay.querySelectorAll(".theme-preset-swatch").forEach((btn) => {
    btn.addEventListener("click", () => setSetting("themePreset", btn.dataset.preset));
  });

  overlay.querySelectorAll("input[data-custom-key]").forEach((input) => {
    input.addEventListener("input", () => {
      const colors = getCustomTheme();
      colors[input.dataset.customKey] = input.value;
      setCustomTheme(colors);
      setSetting("themePreset", "custom", { skipSave: true });
      writeRaw("ati_theme_preset", "custom");
      schedulePreferencesSave();
      syncPanelControls();
    });
  });

  overlay.querySelectorAll("input[data-chat-color]").forEach((input) => {
    input.addEventListener("input", () => setSetting(input.dataset.chatColor, input.value));
  });

  overlay.querySelectorAll("[data-clear-color]").forEach((btn) => {
    btn.addEventListener("click", () => {
      setSetting(btn.dataset.clearColor, "");
      const input = overlay.querySelector(`input[data-chat-color="${btn.dataset.clearColor}"]`);
      if (input) input.value = "#F3F4F6";
    });
  });

  document.getElementById("resetCustomThemeBtn")?.addEventListener("click", () => {
    setCustomTheme({ ...CUSTOM_THEME_DEFAULTS });
    overlay.querySelectorAll("input[data-custom-key]").forEach((input) => {
      input.value = CUSTOM_THEME_DEFAULTS[input.dataset.customKey];
    });
    setSetting("themePreset", "custom");
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
  const chatBehavior = document.getElementById("settingsChatBehaviorSection");
  const onChat = isChatPage();
  if (chatSection) chatSection.classList.toggle("d-none", !onChat);
  if (chatBehavior) chatBehavior.classList.toggle("d-none", !onChat);

  syncPanelControls();
  overlay.classList.remove("d-none");
  overlay.classList.add("settings-overlay--visible");
  overlay.setAttribute("aria-hidden", "false");
  document.body.classList.add("settings-open");
  overlay.querySelector(".settings-drawer")?.focus();
}

function closeSettingsPanel() {
  const overlay = document.getElementById("settingsOverlay");
  if (!overlay) return;
  overlay.classList.remove("settings-overlay--visible");
  overlay.classList.add("d-none");
  overlay.setAttribute("aria-hidden", "true");
  document.body.classList.remove("settings-open");
}

async function resetAllPreferences() {
  PREFERENCE_KEYS.forEach((key) => {
    try {
      localStorage.removeItem(key);
    } catch {
      /* ignore */
    }
  });
  clearCustomThemeVars();
  applyAllSettings();
  syncPanelControls();
  if (isAuthenticated()) {
    try {
      await API.put("/api/user/preferences", {
        ati_theme: "system",
        ati_theme_preset: "default",
        ati_custom_theme: "{}",
        ati_chat_density: "comfortable",
        ati_chat_width: "wide",
        ati_chat_style: "default",
        ati_chat_user_bubble: "",
        ati_chat_assistant_bubble: "",
        ati_chat_accent: "",
        ati_send_on_enter: "true",
        ati_show_chips: "true",
        ati_show_typing: "true",
        ati_auto_scroll: "true",
        ati_reduce_motion: "false",
        ati_ui_animations: "true",
      });
    } catch {
      /* ignore */
    }
  }
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

async function initSettingsPanel() {
  if (!document.getElementById("settingsOverlay")) {
    document.body.insertAdjacentHTML("beforeend", buildPanelHtml());
    bindPanelEvents();
  }
  applyAllSettings();
  bindSettingsTriggers();
  await loadUserPreferences();
}

document.addEventListener("DOMContentLoaded", () => {
  initSettingsPanel().catch(() => {});
});
