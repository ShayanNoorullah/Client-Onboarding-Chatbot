const I18N = {
  en: {
    newChat: "+ New chat",
    searchChats: "Search chats...",
    messagePlaceholder: "Message Client Onboarding Agent...",
    send: "Send",
    logout: "Log out",
    settings: "Settings",
  },
  es: {
    newChat: "+ Nuevo chat",
    searchChats: "Buscar chats...",
    messagePlaceholder: "Mensaje al Agente de Onboarding...",
    send: "Enviar",
    logout: "Cerrar sesión",
    settings: "Configuración",
  },
};

function getLang() {
  return localStorage.getItem("ati_lang") || "en";
}

function t(key) {
  const lang = getLang();
  return (I18N[lang] && I18N[lang][key]) || I18N.en[key] || key;
}

function applyI18n() {
  const map = {
    newChatBtn: "newChat",
    sessionSearch: "searchChats",
    messageInput: "messagePlaceholder",
    logoutBtn: "logout",
  };
  Object.entries(map).forEach(([id, key]) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (el.tagName === "INPUT") el.placeholder = t(key);
    else el.textContent = t(key);
  });
  document.querySelectorAll("[data-open-settings]").forEach((el) => { el.textContent = t("settings"); });
}

window.I18n = { t, getLang, applyI18n, setLang: (l) => { localStorage.setItem("ati_lang", l); applyI18n(); } };
