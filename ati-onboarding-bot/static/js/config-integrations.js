const SAMPLE = {
  event: "brief.created",
  timestamp: "2026-06-08T12:00:00Z",
  data: {
    brief_id: "abc123",
    ref_id: "Client_2026-06-08",
    client_name: "Acme Corp",
    user_email: "client@acme.com",
    project_type: "website_development",
    portal_link: "/portal.html?token=...",
  },
};

async function loadIntegrations() {
  const data = await AdminUtils.apiGet("/api/admin/config/system");
  const c = data.config || {};
  document.getElementById("slackUrl").value = c.slack_webhook_url || "";
  document.getElementById("teamsUrl").value = c.teams_webhook_url || "";
  document.getElementById("docusealUrl").value = c.docuseal_api_url || "";
  document.getElementById("docusealKey").value = c.docuseal_api_key || "";
  document.getElementById("docusealTemplate").value = c.docuseal_nda_template_id || "";
  document.getElementById("samplePayload").textContent = JSON.stringify(SAMPLE, null, 2);
}

async function saveIntegrations() {
  await AdminUtils.apiPut("/api/admin/config/system", {
    slack_webhook_url: document.getElementById("slackUrl").value,
    teams_webhook_url: document.getElementById("teamsUrl").value,
    docuseal_api_url: document.getElementById("docusealUrl").value,
    docuseal_api_key: document.getElementById("docusealKey").value,
    docuseal_nda_template_id: document.getElementById("docusealTemplate").value,
  });
  AdminUtils.showToast("Integrations saved");
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("config-integrations", "INTEGRATIONS", [
    { label: "Dashboard", href: "/admin/dashboard.html" },
    { label: "Configuration" },
    { label: "Integrations" },
  ]);
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  document.getElementById("saveIntegrationsBtn").addEventListener("click", () => saveIntegrations().catch((e) => AdminUtils.showToast(e.message, "error")));
  document.getElementById("copyPayloadBtn").addEventListener("click", () => {
    navigator.clipboard.writeText(document.getElementById("samplePayload").textContent);
    AdminUtils.showToast("Copied");
  });
  loadIntegrations().catch((e) => AdminUtils.showToast(e.message, "error"));
});
