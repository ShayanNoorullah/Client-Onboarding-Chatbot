const MASKED_PASSWORD = "••••••••";
let pageRoot = null;

function smtpEl(id) {
  return (pageRoot || document).querySelector(`#${id}`);
}

async function loadConfig() {
  try {
    const data = await AdminUtils.apiGet("/api/admin/config/smtp");
    const c = data.config;
    if (!c) return;
    smtpEl("smtpHost").value = c.smtp_host || "";
    smtpEl("smtpPort").value = c.smtp_port || 587;
    smtpEl("smtpEncryption").value = c.encryption_protocol || "STARTTLS";
    smtpEl("smtpFrom").value = c.from_email || "";
    smtpEl("smtpUser").value = c.username || "";
    const passEl = smtpEl("smtpPass");
    if (c.password === MASKED_PASSWORD) {
      passEl.value = "";
      passEl.placeholder = "Password saved (enter new value to change)";
    } else {
      passEl.value = c.password || "";
      passEl.placeholder = "";
    }
  } catch (e) { AdminUtils.showToast(e.message, "error"); }
}

async function saveConfig() {
  const body = {
    smtp_host: smtpEl("smtpHost").value,
    smtp_port: +smtpEl("smtpPort").value,
    encryption_protocol: smtpEl("smtpEncryption").value,
    from_email: smtpEl("smtpFrom").value,
    username: smtpEl("smtpUser").value,
    password: smtpEl("smtpPass").value,
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

function bindPasswordToggle() {
  const toggleBtn = smtpEl("togglePass");
  const passInput = smtpEl("smtpPass");
  if (!toggleBtn || !passInput) return;

  toggleBtn.addEventListener("click", () => {
    const show = passInput.type === "password";
    passInput.type = show ? "text" : "password";
    const icon = toggleBtn.querySelector("i");
    if (icon) {
      icon.classList.toggle("fa-eye", !show);
      icon.classList.toggle("fa-eye-slash", show);
    }
    toggleBtn.setAttribute("aria-label", show ? "Hide password" : "Show password");
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("config-smtp", "SMTP CONFIGURATION", [{ label: "Dashboard", href: "/admin/dashboard.html" }, { label: "Configuration" }, { label: "SMTP" }]);
  document.getElementById("adminPageActions").innerHTML = `<button class="btn-admin-primary" id="saveSmtpBtn">Save Configuration</button>`;
  pageRoot = document.getElementById("adminContent");
  pageRoot.appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  document.getElementById("saveSmtpBtn").addEventListener("click", saveConfig);
  smtpEl("testSmtpBtn").addEventListener("click", () => new bootstrap.Modal(document.getElementById("testModal")).show());
  document.getElementById("sendTestBtn").addEventListener("click", testConnection);
  bindPasswordToggle();
  loadConfig();
});
