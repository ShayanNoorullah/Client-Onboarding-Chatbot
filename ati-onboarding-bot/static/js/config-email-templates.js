let templates = [];
let editKey = null;

function renderTable() {
  const tbody = document.getElementById("tplTableBody");
  tbody.innerHTML = templates.length
    ? templates.map((t) => `<tr>
        <td><code>${t.key}</code></td>
        <td>${t.name}</td>
        <td>${t.is_active ? "Active" : "Inactive"}</td>
        <td>
          <button class="action-btn" data-edit="${t.key}">Edit</button>
          <button class="action-btn ms-1" data-preview="${t.key}">Preview</button>
        </td>
      </tr>`).join("")
    : `<tr><td colspan="4" class="admin-empty-state">No templates</td></tr>`;
  tbody.querySelectorAll("[data-edit]").forEach((btn) => {
    btn.addEventListener("click", () => openEditor(btn.dataset.edit));
  });
  tbody.querySelectorAll("[data-preview]").forEach((btn) => {
    btn.addEventListener("click", () => previewTemplate(btn.dataset.preview));
  });
}

function openEditor(key) {
  editKey = key;
  const t = templates.find((x) => x.key === key);
  document.getElementById("tplKey").value = t?.key || "";
  document.getElementById("tplKey").disabled = !!t;
  document.getElementById("tplName").value = t?.name || "";
  document.getElementById("tplSubject").value = t?.subject || "";
  document.getElementById("tplHtml").value = t?.body_html || "";
  document.getElementById("tplText").value = t?.body_text || "";
  document.getElementById("tplActive").checked = t?.is_active !== false;
  bootstrap.Modal.getOrCreateInstance(document.getElementById("tplModal")).show();
}

async function saveTemplate() {
  const body = {
    key: document.getElementById("tplKey").value,
    name: document.getElementById("tplName").value,
    subject: document.getElementById("tplSubject").value,
    body_html: document.getElementById("tplHtml").value,
    body_text: document.getElementById("tplText").value,
    is_active: document.getElementById("tplActive").checked,
    variables: ["client_name", "product_name", "session_link", "brief_link", "brief_summary", "stage"],
  };
  if (editKey) {
    await AdminUtils.apiPut(`/api/admin/config/email-templates/${editKey}`, body);
  } else {
    await AdminUtils.apiPost("/api/admin/config/email-templates", body);
  }
  bootstrap.Modal.getInstance(document.getElementById("tplModal"))?.hide();
  AdminUtils.showToast("Template saved");
  await loadTemplates();
}

async function previewTemplate(key) {
  const data = await AdminUtils.apiPost(`/api/admin/config/email-templates/${key}/preview`, { variables: {} });
  document.getElementById("previewContent").innerHTML = `<strong>${data.subject}</strong><hr>${data.body_html}`;
  bootstrap.Modal.getOrCreateInstance(document.getElementById("previewModal")).show();
}

async function loadTemplates() {
  const data = await AdminUtils.apiGet("/api/admin/config/email-templates");
  templates = data.templates || [];
  renderTable();
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("config-email", "EMAIL TEMPLATES", [
    { label: "Dashboard", href: "/admin/dashboard.html" },
    { label: "Configuration" },
    { label: "Email Templates" },
  ]);
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  document.getElementById("addTplBtn").addEventListener("click", () => { editKey = null; openEditor(null); });
  document.getElementById("saveTplBtn").addEventListener("click", () => saveTemplate().catch((e) => AdminUtils.showToast(e.message, "error")));
  loadTemplates().catch((e) => AdminUtils.showToast(e.message, "error"));
});
