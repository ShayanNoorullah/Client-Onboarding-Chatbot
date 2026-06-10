(function () {
  try {
    var t = localStorage.getItem("ati_theme") || "system";
    if (["system", "light", "dark"].indexOf(t) < 0) t = "system";
    document.documentElement.setAttribute("data-theme", t);

    var preset = localStorage.getItem("ati_theme_preset") || "default";
    var validPresets = ["default", "ocean", "forest", "sunset", "violet", "slate", "high-contrast", "custom"];
    if (validPresets.indexOf(preset) < 0) preset = "default";
    document.documentElement.setAttribute("data-theme-preset", preset);

    if (preset === "custom") {
      var raw = localStorage.getItem("ati_custom_theme") || "{}";
      var custom = JSON.parse(raw);
      var root = document.documentElement.style;
      if (custom.primary) root.setProperty("--custom-primary", custom.primary);
      if (custom.surface) root.setProperty("--custom-surface", custom.surface);
      if (custom.text) root.setProperty("--custom-text", custom.text);
      if (custom.accent) root.setProperty("--custom-accent", custom.accent);
      if (custom.border) root.setProperty("--custom-border", custom.border);
      if (custom.primary) {
        root.setProperty("--custom-muted", custom.surface || custom.primary);
        root.setProperty("--custom-on-primary", custom.text === "#FFFFFF" || custom.text === "#ffffff" ? "#000000" : "#FFFFFF");
      }
    }

    var chatStyle = localStorage.getItem("ati_chat_style");
    if (chatStyle && ["default", "soft", "contrast", "minimal"].indexOf(chatStyle) >= 0) {
      document.documentElement.setAttribute("data-chat-style", chatStyle);
    }
    var userBubble = localStorage.getItem("ati_chat_user_bubble");
    var assistantBubble = localStorage.getItem("ati_chat_assistant_bubble");
    var chatAccent = localStorage.getItem("ati_chat_accent");
    var rs = document.documentElement.style;
    if (userBubble) rs.setProperty("--chat-user-bg", userBubble);
    if (assistantBubble) rs.setProperty("--chat-assistant-bg", assistantBubble);
    if (chatAccent) rs.setProperty("--chat-accent", chatAccent);
  } catch (e) {
    document.documentElement.setAttribute("data-theme", "system");
    document.documentElement.setAttribute("data-theme-preset", "default");
  }
})();
