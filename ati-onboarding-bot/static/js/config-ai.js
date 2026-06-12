const AI_FIELD_MAP = {
  llmProvider: "llm_provider",
  ollamaBaseUrl: "ollama_base_url",
  chatTemperature: "chat_temperature",
  numPredict: "num_predict",
  ragContextMax: "rag_context_max_chars",
  ragKb: "rag_kb_chars",
  ragClient: "rag_client_chars",
  ragMemory: "rag_memory_chars",
  ragLearned: "rag_learned_chars",
  promptVersion: "prompt_version",
};

const REQUIRED_PURPOSES = ["chat", "embed", "vision"];
let aiModels = [];
let editingModelId = null;
let modelModal = null;

function purposeBadges(purposes) {
  return (purposes || []).map((p) => `<span class="badge bg-secondary me-1">${p}</span>`).join("");
}

function renderModelsTable() {
  const tbody = document.getElementById("modelsTableBody");
  if (!tbody) return;
  tbody.innerHTML = aiModels.length
    ? aiModels.map((m) => `<tr>
        <td>${m.name}</td>
        <td>${m.provider}</td>
        <td><code>${m.model_id}</code></td>
        <td>${purposeBadges(m.purposes)}</td>
        <td>${m.is_default ? "Yes" : "—"}</td>
        <td>${m.is_enabled ? "✓" : "×"}</td>
        <td>
          <button type="button" class="action-btn" data-edit-model="${m.id}">Edit</button>
          <button type="button" class="action-btn text-danger" data-delete-model="${m.id}">Delete</button>
        </td></tr>`).join("")
    : `<tr><td colspan="7" class="admin-empty-state">No models configured</td></tr>`;

  tbody.querySelectorAll("[data-edit-model]").forEach((btn) => {
    btn.addEventListener("click", () => openModelModal(btn.dataset.editModel));
  });
  tbody.querySelectorAll("[data-delete-model]").forEach((btn) => {
    btn.addEventListener("click", () => deleteModel(btn.dataset.deleteModel));
  });
}

function validateModels(models) {
  for (const purpose of REQUIRED_PURPOSES) {
    const enabled = models.filter((m) => m.is_enabled && (m.purposes || []).includes(purpose));
    if (!enabled.length) {
      throw new Error(`At least one enabled model must have purpose: ${purpose}`);
    }
    const defaults = enabled.filter((m) => m.is_default);
    if (defaults.length > 1) {
      throw new Error(`Only one default model allowed for purpose: ${purpose}`);
    }
  }
}

function normalizeDefaultFlags(models) {
  const purposes = new Set(models.flatMap((m) => m.purposes || []));
  purposes.forEach((purpose) => {
    const candidates = models.filter((m) => m.is_enabled && m.purposes.includes(purpose));
    if (!candidates.length) return;
    const hasDefault = candidates.some((m) => m.is_default);
    if (!hasDefault) candidates[0].is_default = true;
    else {
      let seen = false;
      candidates.forEach((m) => {
        if (m.is_default) {
          if (seen) m.is_default = false;
          seen = true;
        }
      });
    }
  });
  return models;
}

async function loadAiConfig() {
  const data = await AdminUtils.apiGet("/api/admin/config/ai");
  const c = data.config || {};
  Object.entries(AI_FIELD_MAP).forEach(([elId, key]) => {
    const el = document.getElementById(elId);
    if (el && c[key] !== undefined && c[key] !== null) el.value = c[key];
  });
  aiModels = (c.models || []).map((m) => ({ ...m }));
  renderModelsTable();
}

function openModelModal(id) {
  editingModelId = id || null;
  document.getElementById("modelModalTitle").textContent = id ? "Edit Model" : "Add Model";
  const model = id ? aiModels.find((m) => m.id === id) : null;
  document.getElementById("modelName").value = model?.name || "";
  document.getElementById("modelProvider").value = model?.provider || "ollama";
  document.getElementById("modelId").value = model?.model_id || "";
  document.getElementById("modelTemperature").value = model?.temperature ?? 0.3;
  document.getElementById("modelMaxTokens").value = model?.max_tokens ?? 512;
  document.getElementById("modelEnabled").checked = model?.is_enabled !== false;
  document.getElementById("modelDefault").checked = model?.is_default === true;
  document.querySelectorAll(".purpose-cb").forEach((cb) => {
    cb.checked = (model?.purposes || []).includes(cb.value);
  });
  modelModal.show();
}

function deleteModel(id) {
  if (!confirm("Remove this model profile?")) return;
  aiModels = aiModels.filter((m) => m.id !== id);
  renderModelsTable();
}

function saveModelFromModal() {
  const purposes = [...document.querySelectorAll(".purpose-cb:checked")].map((cb) => cb.value);
  if (!purposes.length) {
    AdminUtils.showToast("Select at least one purpose", "warning");
    return;
  }
  const payload = {
    id: editingModelId || crypto.randomUUID().slice(0, 8),
    name: document.getElementById("modelName").value.trim(),
    provider: document.getElementById("modelProvider").value,
    model_id: document.getElementById("modelId").value.trim(),
    purposes,
    temperature: parseFloat(document.getElementById("modelTemperature").value) || 0.3,
    max_tokens: parseInt(document.getElementById("modelMaxTokens").value, 10) || 512,
    is_enabled: document.getElementById("modelEnabled").checked,
    is_default: document.getElementById("modelDefault").checked,
  };
  if (!payload.name || !payload.model_id) {
    AdminUtils.showToast("Name and Model ID are required", "warning");
    return;
  }

  if (payload.is_default) {
    purposes.forEach((purpose) => {
      aiModels.forEach((m) => {
        if (m.purposes.includes(purpose)) m.is_default = false;
      });
    });
  }

  const idx = aiModels.findIndex((m) => m.id === payload.id);
  if (idx >= 0) aiModels[idx] = payload;
  else aiModels.push(payload);

  aiModels = normalizeDefaultFlags(aiModels);
  modelModal.hide();
  renderModelsTable();
}

async function saveAiConfig() {
  aiModels = normalizeDefaultFlags(aiModels);
  validateModels(aiModels);
  const body = {};
  Object.entries(AI_FIELD_MAP).forEach(([elId, key]) => {
    const el = document.getElementById(elId);
    if (!el) return;
    body[key] = el.type === "number" ? +el.value : el.value;
  });
  body.models = aiModels;
  await AdminUtils.apiPut("/api/admin/config/ai", body);
  AdminUtils.showToast("AI configuration saved");
  await loadAiConfig();
}

async function testOllama() {
  const data = await AdminUtils.apiPost("/api/admin/config/ai/test-ollama", {});
  const pre = document.getElementById("ollamaResult");
  pre.style.display = "block";
  pre.textContent = JSON.stringify(data, null, 2);
  AdminUtils.showToast(
    data.ollama_reachable ? "Ollama reachable" : "Ollama unreachable",
    data.ollama_reachable ? "success" : "warning",
  );
}

async function pullFromOllama() {
  const data = await AdminUtils.apiGet("/api/admin/config/ai/ollama-models");
  if (!data.reachable) {
    AdminUtils.showToast("Ollama is not reachable", "warning");
    return;
  }
  const existing = new Set(aiModels.map((m) => m.model_id));
  let added = 0;
  (data.models || []).forEach((name) => {
    if (existing.has(name)) return;
    aiModels.push({
      id: crypto.randomUUID().slice(0, 8),
      name,
      provider: "ollama",
      model_id: name,
      purposes: [],
      temperature: 0.3,
      max_tokens: 512,
      is_enabled: false,
      is_default: false,
    });
    added += 1;
  });
  renderModelsTable();
  AdminUtils.showToast(added ? `Added ${added} model(s) from Ollama` : "No new models to add");
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await AdminUtils.checkAdminAuth()) return;
  initAdminLayout("config-ai", "AI CONFIGURATION", [
    { label: "Dashboard", href: "/admin/dashboard.html" },
    { label: "Configuration" },
    { label: "AI Configuration" },
  ]);
  document.getElementById("adminContent").appendChild(document.getElementById("pageTemplate").content.cloneNode(true));
  modelModal = new bootstrap.Modal(document.getElementById("modelModal"));

  document.getElementById("saveAiBtn").addEventListener("click", () => saveAiConfig().catch((e) => AdminUtils.showToast(AdminUtils.formatApiError(e), "error")));
  document.getElementById("testOllamaBtn").addEventListener("click", () => testOllama().catch((e) => AdminUtils.showToast(AdminUtils.formatApiError(e), "error")));
  document.getElementById("addModelBtn").addEventListener("click", () => openModelModal(null));
  document.getElementById("saveModelBtn").addEventListener("click", saveModelFromModal);
  document.getElementById("pullOllamaBtn").addEventListener("click", () => pullFromOllama().catch((e) => AdminUtils.showToast(AdminUtils.formatApiError(e), "error")));

  loadAiConfig().catch((e) => AdminUtils.showToast(AdminUtils.formatApiError(e), "error"));
});
