const FIELD_MAP = {
  maxUpload: "max_upload_size_mb",
  maxFiles: "max_files_per_session",
  productName: "product_name",
  supportEmail: "support_email",
  privacyUrl: "privacy_url",
  phone: "phone",
};

function parseEmailList(value) {
  return (value || "").split(",").map((s) => s.trim()).filter(Boolean);
}

function formatEmailList(arr) {
  return (arr || []).join(", ");
}

async function loadSystemConfig() {
  const data = await AdminUtils.apiGet("/api/admin/config/system");
  const c = data.config || {};
  Object.entries(FIELD_MAP).forEach(([elId, key]) => {
    const el = document.getElementById(elId);
    if (el && c[key] !== undefined) el.value = c[key];
  });
  document.getElementById("emailNotif").checked = c.email_notifications_enabled !== false;
  document.getElementById("followUp").checked = c.follow_up_enabled !== false;
  document.getElementById("surfEnabled").checked = c.surf_enabled !== false;
  if (document.getElementById("maxUrls")) {
    document.getElementById("maxUrls").value = c.max_urls_per_session ?? 5;
  }
  document.getElementById("notifTo").value = formatEmailList(c.notification_to_emails);
  document.getElementById("notifCc").value = formatEmailList(c.notification_cc_emails);
  if (document.getElementById("defaultLang")) {
    document.getElementById("defaultLang").value = c.default_language || "en";
  }
}

async function saveSystemConfig() {
  const body = {};
  Object.entries(FIELD_MAP).forEach(([elId, key]) => {
    const el = document.getElementById(elId);
    if (!el) return;
    body[key] = el.type === "number" ? +el.value : el.value;
  });
  body.email_notifications_enabled = document.getElementById("emailNotif").checked;
  body.follow_up_enabled = document.getElementById("followUp").checked;
  body.surf_enabled = document.getElementById("surfEnabled").checked;
  const maxUrlsEl = document.getElementById("maxUrls");
  if (maxUrlsEl) body.max_urls_per_session = +maxUrlsEl.value;
  body.notification_to_emails = parseEmailList(document.getElementById("notifTo").value);
  body.notification_cc_emails = parseEmailList(document.getElementById("notifCc").value);
  const langEl = document.getElementById("defaultLang");
  if (langEl) body.default_language = langEl.value;
  await AdminUtils.apiPut("/api/admin/config/system", body);
  AdminUtils.showToast("System configuration saved");
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("config-system", "SYSTEM CONFIGURATION", [
    { label: "Dashboard", href: "/admin/dashboard.html" },
    { label: "Configuration" },
    { label: "System Configuration" },
  ]);
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  document.getElementById("saveSystemBtn").addEventListener("click", () => saveSystemConfig().catch((e) => AdminUtils.showToast(e.message, "error")));
  loadSystemConfig().catch((e) => AdminUtils.showToast(e.message, "error"));
});
