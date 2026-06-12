async function loadLearningReport() {
  const data = await AdminUtils.apiGet("/api/admin/learning/report");
  const cards = document.getElementById("accuracyCards");
  const accuracy = data.accuracy_by_task || [];
  cards.innerHTML = accuracy.length
    ? accuracy.map((a) => `<div class="col-md-3"><div class="stat-card"><div class="stat-label">${a.task_type}</div><div class="stat-value">${a.accuracy_pct}%</div><div class="small text-secondary">+${a.positive_count} / -${a.negative_count}</div></div></div>`).join("")
    : `<div class="col-12 text-secondary">No feedback accuracy data yet.</div>`;

  document.getElementById("activePrompts").textContent = JSON.stringify(data.active_prompts || [], null, 2);

  const fbBody = document.getElementById("feedbackBody");
  const feedback = data.recent_feedback || [];
  fbBody.innerHTML = feedback.length
    ? feedback.map((f) => `<tr><td>${f.feedback_type}</td><td>${f.signal}</td><td>${f.task_type || "—"}</td><td>${AdminUtils.formatDate(f.created_at)}</td></tr>`).join("")
    : `<tr><td colspan="4" class="admin-empty-state">No feedback yet</td></tr>`;

  const valBody = document.getElementById("validationBody");
  const validations = data.recent_validations || [];
  valBody.innerHTML = validations.length
    ? validations.map((v) => `<tr><td>${v.prompt_name} (${v.prompt_version_id})</td><td>${v.failures_fixed}</td><td>${v.regressions}</td><td>${v.confidence}</td><td>${v.promoted ? "Yes" : "No"}</td></tr>`).join("")
    : `<tr><td colspan="5" class="admin-empty-state">No validation runs yet</td></tr>`;
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("config-learning", "AGENT LEARNING", [
    { label: "Dashboard", href: "/admin/dashboard.html" },
    { label: "Configuration" },
    { label: "Learning" },
  ]);
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  loadLearningReport().catch((e) => AdminUtils.showToast(AdminUtils.formatApiError(e), "error"));
});
