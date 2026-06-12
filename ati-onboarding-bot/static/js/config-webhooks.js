let whModal;

async function loadWebhooks() {
  const data = await AdminUtils.apiGet("/api/admin/webhooks");
  const tbody = document.getElementById("webhooksBody");
  const hooks = data.webhooks || [];
  tbody.innerHTML = hooks.length ? hooks.map((w) => `<tr>
    <td>${w.name}</td><td class="text-truncate" style="max-width:200px">${w.url}</td>
    <td>${(w.event_types || []).join(", ") || "all"}</td>
    <td>${w.is_active ? "✓" : "×"}</td>
    <td><button class="action-btn" data-edit="${w.id}">Edit</button>
    <button class="action-btn" data-test="${w.id}">Test</button>
    <button class="action-btn action-btn-danger" data-del="${w.id}">Delete</button></td></tr>`).join("")
    : `<tr><td colspan="5" class="admin-empty-state">No webhooks</td></tr>`;
  tbody.querySelectorAll("[data-edit]").forEach((b) => b.addEventListener("click", () => openWebhook(b.dataset.edit, hooks)));
  tbody.querySelectorAll("[data-test]").forEach((b) => b.addEventListener("click", () => testWebhook(b.dataset.test)));
  tbody.querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", () => deleteWebhook(b.dataset.del)));
  const del = await AdminUtils.apiGet("/api/admin/webhooks/deliveries?limit=20");
  document.getElementById("deliveriesBody").innerHTML = (del.deliveries || []).map((d) =>
    `<tr><td>${d.event_type}</td><td>${d.status}</td><td>${d.attempts}</td><td>${d.last_error || "—"}</td></tr>`
  ).join("") || `<tr><td colspan="4">No deliveries yet</td></tr>`;
}

function openWebhook(id, hooks) {
  const w = hooks.find((h) => h.id === id) || {};
  document.getElementById("whId").value = id || "";
  document.getElementById("whName").value = w.name || "";
  document.getElementById("whUrl").value = w.url || "";
  document.getElementById("whSecret").value = "";
  document.getElementById("whEvents").value = (w.event_types || []).join(", ");
  whModal.show();
}

async function saveWebhook() {
  const id = document.getElementById("whId").value;
  const body = {
    name: document.getElementById("whName").value,
    url: document.getElementById("whUrl").value,
    secret: document.getElementById("whSecret").value,
    event_types: document.getElementById("whEvents").value.split(",").map((s) => s.trim()).filter(Boolean),
  };
  if (id) await AdminUtils.apiPut(`/api/admin/webhooks/${id}`, body);
  else await AdminUtils.apiPost("/api/admin/webhooks", body);
  whModal.hide();
  AdminUtils.showToast("Webhook saved");
  loadWebhooks();
}

async function testWebhook(id) {
  const r = await AdminUtils.apiPost(`/api/admin/webhooks/${id}/test`, {});
  AdminUtils.showToast(r.delivery?.status === "delivered" ? "Test delivered" : (r.delivery?.last_error || "Test sent"), r.delivery?.status === "delivered" ? "success" : "warning");
  loadWebhooks();
}

async function deleteWebhook(id) {
  if (!confirm("Delete webhook?")) return;
  await AdminUtils.apiDelete(`/api/admin/webhooks/${id}`);
  loadWebhooks();
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("config-webhooks", "WEBHOOKS", [
    { label: "Dashboard", href: "/admin/dashboard.html" },
    { label: "Configuration" },
    { label: "Webhooks" },
  ]);
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  whModal = new bootstrap.Modal(document.getElementById("webhookModal"));
  document.getElementById("addWebhookBtn").addEventListener("click", () => openWebhook("", []));
  document.getElementById("saveWebhookBtn").addEventListener("click", () => saveWebhook().catch((e) => AdminUtils.showToast(e.message, "error")));
  loadWebhooks().catch((e) => AdminUtils.showToast(e.message, "error"));
});
