async function loadTenant() {
  const data = await AdminUtils.apiGet("/api/admin/tenants/current");
  const t = data.tenant || {};
  document.getElementById("tenantName").value = t.name || "";
  document.getElementById("tenantSlug").value = t.slug || "";
  document.getElementById("tenantPlan").value = t.plan || "free";
  document.getElementById("tenantStatus").value = t.status || "active";
  document.getElementById("tenantDomain").value = t.custom_domain || "";
  const branding = t.branding || {};
  document.getElementById("logoUrl").value = branding.logo_url || "";
  document.getElementById("primaryColor").value = branding.primary_color || "#0D0D0D";
  const limits = t.limits || {};
  document.getElementById("limitUsers").value = limits.max_users ?? 50;
  document.getElementById("limitSessions").value = limits.max_sessions_per_month ?? 500;
  document.getElementById("limitStorage").value = limits.max_storage_mb ?? 1024;
  if (branding.primary_color) {
    document.documentElement.style.setProperty("--primary", branding.primary_color);
  }
}

async function saveTenant() {
  const body = {
    name: document.getElementById("tenantName").value.trim(),
    plan: document.getElementById("tenantPlan").value,
    status: document.getElementById("tenantStatus").value,
    custom_domain: document.getElementById("tenantDomain").value.trim() || null,
    branding: {
      logo_url: document.getElementById("logoUrl").value.trim(),
      primary_color: document.getElementById("primaryColor").value,
    },
    limits: {
      max_users: +document.getElementById("limitUsers").value,
      max_sessions_per_month: +document.getElementById("limitSessions").value,
      max_storage_mb: +document.getElementById("limitStorage").value,
    },
  };
  await AdminUtils.apiPatch("/api/admin/tenants/current", body);
  AdminUtils.showToast("Workspace saved");
  await loadTenant();
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("config-tenant", "WORKSPACE", [
    { label: "Dashboard", href: "/admin/dashboard.html" },
    { label: "Configuration" },
    { label: "Workspace" },
  ]);
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  document.getElementById("saveTenantBtn").addEventListener("click", () => saveTenant().catch((e) => AdminUtils.showToast(AdminUtils.formatApiError(e), "error")));
  loadTenant().catch((e) => AdminUtils.showToast(AdminUtils.formatApiError(e), "error"));
});
