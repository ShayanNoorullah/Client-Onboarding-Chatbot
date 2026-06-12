async function loadConfig() {
  try {
    const data = await AdminUtils.apiGet("/api/admin/config/smtp");
    const c = data.config;
    if (!c) return;
    document.getElementById("smtpHost").value = c.smtp_host || "";
    document.getElementById("smtpPort").value = c.smtp_port || 587;
    document.getElementById("smtpEncryption").value = c.encryption_protocol || "STARTTLS";
    document.getElementById("smtpFrom").value = c.from_email || "";
    document.getElementById("smtpUser").value = c.username || "";
    document.getElementById("smtpPass").value = c.password || "";
  } catch (e) { AdminUtils.showToast(e.message, "error"); }
}

async function saveConfig() {
  const body = {
    smtp_host: document.getElementById("smtpHost").value,
    smtp_port: +document.getElementById("smtpPort").value,
    encryption_protocol: document.getElementById("smtpEncryption").value,
    from_email: document.getElementById("smtpFrom").value,
    username: document.getElementById("smtpUser").value,
    password: document.getElementById("smtpPass").value,
  };
  try {
    await AdminUtils.apiPut("/api/admin/config/smtp", body);
    AdminUtils.showToast("SMTP configuration saved");
    loadConfig();
  } catch (e) { AdminUtils.showToast(e.message, "error"); }
}

async function testConnection() {
  const email = document.getElementById("testEmail").value;
  if (!email) { AdminUtils.showToast("Enter a test email", "warning"); return; }
  try {
    const data = await AdminUtils.apiPost("/api/admin/config/smtp/test", { test_email: email });
    AdminUtils.showToast(data.message, data.success ? "success" : "error");
    bootstrap.Modal.getInstance(document.getElementById("testModal"))?.hide();
  } catch (e) { AdminUtils.showToast(e.message, "error"); }
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("config-smtp", "SMTP CONFIGURATION", [{ label: "Dashboard", href: "/admin/dashboard.html" }, { label: "Configuration" }, { label: "SMTP" }]);
  document.getElementById("adminPageActions").innerHTML = `<button class="btn-admin-primary" id="saveSmtpBtn">Save Configuration</button>`;
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  document.getElementById("saveSmtpBtn").addEventListener("click", saveConfig);
  document.getElementById("testSmtpBtn").addEventListener("click", () => new bootstrap.Modal(document.getElementById("testModal")).show());
  document.getElementById("sendTestBtn").addEventListener("click", testConnection);
  document.getElementById("togglePass").addEventListener("click", () => {
    const inp = document.getElementById("smtpPass");
    inp.type = inp.type === "password" ? "text" : "password";
  });
  loadConfig();
});
