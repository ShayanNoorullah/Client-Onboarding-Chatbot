let rules = [];

function renderRules() {
  const tbody = document.getElementById("rulesTableBody");
  tbody.innerHTML = rules.map((r, i) => `<tr>
    <td><select class="form-select form-select-sm" data-field="trigger" data-idx="${i}">
      <option value="session_idle" ${r.trigger === "session_idle" ? "selected" : ""}>Session Idle</option>
      <option value="stage_stuck" ${r.trigger === "stage_stuck" ? "selected" : ""}>Stage Stuck</option>
      <option value="brief_complete" ${r.trigger === "brief_complete" ? "selected" : ""}>Brief Complete</option>
    </select></td>
    <td><input class="form-control form-control-sm" data-field="delay_hours" data-idx="${i}" type="number" value="${r.delay_hours}"></td>
    <td><input class="form-control form-control-sm" data-field="template_key" data-idx="${i}" value="${r.template_key}"></td>
    <td><input type="checkbox" data-field="is_active" data-idx="${i}" ${r.is_active ? "checked" : ""}></td>
    <td><input class="form-control form-control-sm" data-field="max_sends" data-idx="${i}" type="number" value="${r.max_sends}"></td>
  </tr>`).join("");

  tbody.querySelectorAll("[data-field]").forEach((el) => {
    el.addEventListener("change", () => {
      const idx = +el.dataset.idx;
      const field = el.dataset.field;
      rules[idx][field] = el.type === "checkbox" ? el.checked : (el.type === "number" ? +el.value : el.value);
    });
  });
}

async function loadRules() {
  const data = await AdminUtils.apiGet("/api/admin/config/follow-up-rules");
  rules = data.rules || [];
  renderRules();
}

async function saveRules() {
  await AdminUtils.apiPut("/api/admin/config/follow-up-rules", {
    rules: rules.map((r) => ({
      id: r.id,
      trigger: r.trigger,
      delay_hours: r.delay_hours,
      template_key: r.template_key,
      is_active: r.is_active,
      max_sends: r.max_sends,
    })),
  });
  AdminUtils.showToast("Follow-up rules saved");
  await loadRules();
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("config-followup", "FOLLOW-UP TIMING", [
    { label: "Dashboard", href: "/admin/dashboard.html" },
    { label: "Configuration" },
    { label: "Follow-up Timing" },
  ]);
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  document.getElementById("addRuleBtn").addEventListener("click", () => {
    rules.push({ trigger: "session_idle", delay_hours: 24, template_key: "session_reminder", is_active: true, max_sends: 3 });
    renderRules();
  });
  document.getElementById("saveRulesBtn").addEventListener("click", () => saveRules().catch((e) => AdminUtils.showToast(e.message, "error")));
  loadRules().catch((e) => AdminUtils.showToast(e.message, "error"));
});
