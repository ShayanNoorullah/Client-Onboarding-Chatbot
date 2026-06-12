let reportData = null;

async function loadReport() {
  AdminUtils.setStatsLoading(["rptUsers", "rptSessions", "rptBriefs", "rptCompletion"]);
  reportData = await AdminUtils.apiGet("/api/admin/dashboard");
  const from = document.getElementById("dateFrom").value;
  const to = document.getElementById("dateTo").value;

  AdminUtils.setStatValue("rptUsers", reportData.total_users);
  AdminUtils.setStatValue("rptSessions", reportData.total_sessions);
  AdminUtils.setStatValue("rptBriefs", reportData.completed_briefs);
  AdminUtils.setStatValue("rptCompletion", `${reportData.completion_rate}%`);

  let activity = reportData.activity_by_day || [];
  if (from) activity = activity.filter((r) => r.date >= from);
  if (to) activity = activity.filter((r) => r.date <= to);

  if (typeof Chart !== "undefined") {
    const lineCtx = document.getElementById("lineChart");
    if (lineCtx._chart) lineCtx._chart.destroy();
    lineCtx._chart = new Chart(lineCtx, {
      type: "line",
      data: {
        labels: activity.map((r) => r.date),
        datasets: [{ label: "Sessions", data: activity.map((r) => r.sessions), borderColor: "var(--primary, #0D0D0D)", tension: 0.3 }],
      },
      options: { responsive: true },
    });

    const stages = reportData.sessions_by_stage || {};
    const doughCtx = document.getElementById("doughnutChart");
    if (doughCtx._chart) doughCtx._chart.destroy();
    doughCtx._chart = new Chart(doughCtx, {
      type: "doughnut",
      data: { labels: Object.keys(stages), datasets: [{ data: Object.values(stages), backgroundColor: ["#0D0D0D","#6B7280","#9CA3AF","#D1D5DB","#E5E7EB","#F3F4F6"] }] },
      options: { responsive: true },
    });

    const pts = reportData.project_types || {};
    const barCtx = document.getElementById("barChart");
    if (barCtx._chart) barCtx._chart.destroy();
    barCtx._chart = new Chart(barCtx, {
      type: "bar",
      data: { labels: Object.keys(pts), datasets: [{ label: "Sessions", data: Object.values(pts), backgroundColor: "#0D0D0D" }] },
      options: { responsive: true, plugins: { legend: { display: false } } },
    });
  }
}

function exportCSV() {
  const from = document.getElementById("dateFrom").value;
  const to = document.getElementById("dateTo").value;
  let url = "/api/admin/reports/export?";
  if (from) url += `from_date=${from}&`;
  if (to) url += `to_date=${to}`;
  window.location = url;
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("reports", "REPORTS", [{ label: "Dashboard", href: "/admin/dashboard.html" }, { label: "Reports" }]);
  document.getElementById("adminPageActions").innerHTML = `<button class="btn-admin-primary" id="exportBtn">Download CSV</button>`;
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  const today = new Date().toISOString().slice(0, 10);
  const weekAgo = new Date(Date.now() - 7 * 86400000).toISOString().slice(0, 10);
  document.getElementById("dateFrom").value = weekAgo;
  document.getElementById("dateTo").value = today;
  document.getElementById("applyDates").addEventListener("click", loadReport);
  document.getElementById("exportBtn").addEventListener("click", exportCSV);
  loadReport();
});
