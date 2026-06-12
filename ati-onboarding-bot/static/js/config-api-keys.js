let keyModal = null;

async function loadKeys() {
  const data = await AdminUtils.apiGet("/api/admin/tenants/api-keys");
  const tbody = document.getElementById("keysTableBody");
  const keys = data.api_keys || [];
  tbody.innerHTML = keys.length ? keys.map((k) => `<tr>
    <td>${k.name}</td><td><code>${k.key_prefix}…</code></td>
    <td>${AdminUtils.formatDate(k.created_at)}</td>
    <td>${k.is_active ? "Active" : "Revoked"}</td>
    <td>${k.is_active ? `<button class="action-btn text-danger" data-revoke="${k.id}">Revoke</button>` : "—"}</td></tr>`).join("")
    : `<tr><td colspan="5" class="admin-empty-state">No API keys</td></tr>`;
  tbody.querySelectorAll("[data-revoke]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!await AdminUtils.showConfirm("Revoke this API key?")) return;
      await AdminUtils.apiDelete(`/api/admin/tenants/api-keys/${btn.dataset.revoke}`);
      AdminUtils.showToast("Key revoked");
      loadKeys();
    });
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("config-api-keys", "API KEYS", [
    { label: "Dashboard", href: "/admin/dashboard.html" },
    { label: "Configuration" },
    { label: "API Keys" },
  ]);
  document.getElementById("adminPageActions").innerHTML = `<button class="btn-admin-primary" id="addKeyBtn">+ Create Key</button>`;
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  keyModal = new bootstrap.Modal(document.getElementById("keyModal"));
  document.getElementById("addKeyBtn").addEventListener("click", () => keyModal.show());
  document.getElementById("createKeyBtn").addEventListener("click", async () => {
    const name = document.getElementById("keyName").value.trim();
    if (!name) return AdminUtils.showToast("Enter a key name", "warning");
    const data = await AdminUtils.apiPost("/api/admin/tenants/api-keys", { name });
    keyModal.hide();
    const pre = document.getElementById("newKeyDisplay");
    pre.classList.remove("d-none");
    pre.textContent = `Copy this key now — it won't be shown again:\n\n${data.api_key.key}`;
    AdminUtils.showToast("API key created");
    loadKeys();
  });
  loadKeys().catch((e) => AdminUtils.showToast(AdminUtils.formatApiError(e), "error"));
});
