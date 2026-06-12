const FIELD_MAP = {
  maxUpload: "max_upload_size_mb",
  maxFiles: "max_files_per_session",
  productName: "product_name",
  supportEmail: "support_email",
  privacyUrl: "privacy_url",
  phone: "phone",
};

async function loadSystemConfig() {
  const data = await AdminUtils.apiGet("/api/admin/config/system");
  const c = data.config || {};
  Object.entries(FIELD_MAP).forEach(([elId, key]) => {
    const el = document.getElementById(elId);
    if (el && c[key] !== undefined) el.value = c[key];
  });
  document.getElementById("emailNotif").checked = c.email_notifications_enabled !== false;
  document.getElementById("followUp").checked = c.follow_up_enabled !== false;
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
