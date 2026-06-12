async function loadPipelineData() {
  AdminUtils.setStatsLoading(["ptTotal", "ptCompleted", "ptInProgress", "ptAbandoned"]);
  const data = await AdminUtils.apiGet("/api/admin/pipeline/project-types");
  const summary = data.summary || {};
  AdminUtils.setStatValue("ptTotal", summary.total ?? 0);
  AdminUtils.setStatValue("ptCompleted", summary.completed ?? 0);
  AdminUtils.setStatValue("ptInProgress", summary.in_progress ?? 0);
  AdminUtils.setStatValue("ptAbandoned", summary.abandoned ?? 0);

  const rows = data.project_types || [];
  const labels = rows.map((r) => r.project_type);
  const values = rows.map((r) => r.total);

  if (typeof Chart !== "undefined" && labels.length) {
    const primary = getComputedStyle(document.documentElement).getPropertyValue("--primary").trim() || "#0D0D0D";
    new Chart(document.getElementById("ptChart"), {
      type: "bar",
      data: { labels, datasets: [{ label: "Sessions", data: values, backgroundColor: primary }] },
      options: { responsive: true, plugins: { legend: { display: false } } },
    });
  }

  const tbody = document.getElementById("ptTableBody");
  tbody.innerHTML = rows.length
    ? rows.map((r) => `<tr>
        <td>${r.project_type}</td><td>${r.total}</td><td>${r.completed}</td><td>${r.in_progress}</td>
        <td>${r.last_activity ? AdminUtils.formatDate(r.last_activity) : "—"}</td></tr>`).join("")
    : `<tr><td colspan="5" class="admin-empty-state">No data</td></tr>`;
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("pipeline-types", "PIPELINE - PROJECT TYPES", [
    { label: "Dashboard", href: "/admin/dashboard.html" },
    { label: "Pipeline" },
    { label: "Project Types" },
  ]);
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  loadPipelineData().catch((e) => AdminUtils.showToast(e.message, "error"));
});
