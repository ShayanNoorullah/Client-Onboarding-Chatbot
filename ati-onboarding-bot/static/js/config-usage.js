async function loadUsage() {
  AdminUtils.setStatsLoading(["usageUsers", "usageSessions", "usageStorage"]);
  const data = await AdminUtils.apiGet("/api/admin/tenants/usage");
  const usage = data.usage || {};
  const limits = data.limits || {};
  AdminUtils.setStatValue("usageUsers", usage.users_count ?? 0);
  AdminUtils.setStatValue("usageSessions", usage.sessions_count ?? 0);
  AdminUtils.setStatValue("usageStorage", Math.round((usage.storage_bytes ?? 0) / (1024 * 1024)));
  document.getElementById("limitUsersLabel").textContent = `Limit: ${limits.max_users ?? "—"}`;
  document.getElementById("limitSessionsLabel").textContent = `Limit: ${limits.max_sessions_per_month ?? "—"}`;
  document.getElementById("limitStorageLabel").textContent = `Limit: ${limits.max_storage_mb ?? "—"} MB`;
  document.getElementById("usageTable").innerHTML = `
    <tr><td>Tenant</td><td>${data.tenant_id || "—"}</td></tr>
    <tr><td>Period</td><td>${usage.period || "current"}</td></tr>
    <tr><td>Last updated</td><td>${usage.updated_at ? AdminUtils.formatDate(usage.updated_at) : "—"}</td></tr>`;
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("config-usage", "USAGE & LIMITS", [
    { label: "Dashboard", href: "/admin/dashboard.html" },
    { label: "Configuration" },
    { label: "Usage & Limits" },
  ]);
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  loadUsage().catch((e) => AdminUtils.showToast(AdminUtils.formatApiError(e), "error"));
});
