let auditPage = 1, auditLimit = 25, auditSearch = "";

async function loadAudit() {
  const tbody = document.getElementById("auditTableBody");
  tbody.innerHTML = `<tr><td colspan="5" class="admin-loading"><div class="spinner-border spinner-border-sm"></div></td></tr>`;
  const q = auditSearch ? `&search=${encodeURIComponent(auditSearch)}` : "";
  const data = await AdminUtils.apiGet(`/api/admin/audit?page=${auditPage}&limit=${auditLimit}${q}`);
  const events = data.events || [];
  tbody.innerHTML = events.length ? events.map((e) => `<tr>
    <td>${AdminUtils.formatDate(e.created_at)}</td>
    <td>${e.actor_email}</td><td>${e.action}</td><td>${e.resource}</td>
    <td><code class="small">${JSON.stringify(e.details || {})}</code></td></tr>`).join("")
    : `<tr><td colspan="5" class="admin-empty-state">No audit events</td></tr>`;
  AdminUtils.renderPagination(document.getElementById("auditPagination"), data.page, data.total, data.pages, (p) => {
    auditPage = p;
    loadAudit();
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("settings-audit", "AUDIT LOG", [
    { label: "Dashboard", href: "/admin/dashboard.html" },
    { label: "Settings" },
    { label: "Audit Log" },
  ]);
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  AdminUtils.renderTableControls(document.getElementById("tableControls"), auditLimit, (n) => {
    auditLimit = n;
    auditPage = 1;
    loadAudit();
  }, (q) => {
    auditSearch = q;
    auditPage = 1;
    loadAudit();
  });
  loadAudit().catch((e) => AdminUtils.showToast(AdminUtils.formatApiError(e), "error"));
});
