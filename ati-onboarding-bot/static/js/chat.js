let currentUser = null;
let sessionId = null;
let ws = null;
let waiting = false;

function linkify(text) {
  return text.replace(
    /(https?:\/\/[^\s]+)/g,
    '<a href="$1" target="_blank" rel="noopener">$1</a>'
  );
}

function updateEmptyState() {
  const container = document.getElementById("messages");
  const empty = document.getElementById("emptyState");
  if (!empty) return;
  const hasMessages = container && container.children.length > 0;
  empty.classList.toggle("d-none", hasMessages);
}

function clearMessages() {
  const container = document.getElementById("messages");
  if (container) container.innerHTML = "";
  updateEmptyState();
}

function appendMessage(role, content) {
  if (!content?.trim()) return;
  const container = document.getElementById("messages");
  const row = document.createElement("div");
  row.className = `msg-row ${role}`;
  row.innerHTML = `<div class="msg-bubble">${linkify(content)}</div>`;
  container.appendChild(row);
  container.scrollTop = container.scrollHeight;
  updateEmptyState();
}

function renderHistory(messages) {
  clearMessages();
  (messages || []).forEach((m) => {
    if (m.role === "user" || m.role === "assistant") {
      appendMessage(m.role, m.content);
    }
  });
}

function showTyping(show) {
  const el = document.getElementById("typing");
  if (el) el.classList.toggle("d-none", !show);
}

function setSendEnabled(enabled) {
  const btn = document.getElementById("sendBtn");
  if (btn) btn.disabled = !enabled || waiting;
}

function renderChips(suggestions) {
  const area = document.getElementById("chips");
  area.innerHTML = "";
  (suggestions || []).forEach((text) => {
    const chip = document.createElement("button");
    chip.className = "chip";
    chip.textContent = text;
    chip.onclick = () => sendMessage(text);
    area.appendChild(chip);
  });
}

function updateDownloadBtn(data) {
  const btn = document.getElementById("downloadBrief");
  if (!btn) return;
  if (data.done && data.brief_download_url) {
    btn.classList.remove("d-none");
    btn.href = data.brief_download_url;
  } else {
    btn.classList.add("d-none");
  }
}

function updateStatus(data) {
  const status = document.getElementById("status");
  if (!status) return;
  if (data.auto_summarising) {
    status.textContent = "Generating your brief...";
  } else if (data.done) {
    status.textContent = "Brief ready";
  } else if (data.requirements_complete) {
    status.textContent = "Almost ready";
  } else if (data.stage) {
    status.textContent = data.consent_given ? "Gathering requirements" : "Awaiting consent";
  } else {
    status.textContent = "Connected";
  }
}

function handleServerMessage(data) {
  waiting = false;
  showTyping(false);
  setSendEnabled(true);

  if (data.messages?.length) {
    renderHistory(data.messages);
  } else if (data.content?.trim()) {
    appendMessage("assistant", data.content);
  }

  renderChips(data.suggestions);
  updateDownloadBtn(data);
  updateStatus(data);
}

async function loadSessionHistory(id) {
  try {
    const data = await API.get(`/api/user/sessions/${id}`);
    renderHistory(data.messages);
    updateDownloadBtn(data);
    updateStatus(data);
    return data;
  } catch {
    return null;
  }
}

function connectWS() {
  if (!sessionId) return;
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  ws = new WebSocket(`${proto}//${location.host}/ws/chat/${sessionId}`);

  ws.onopen = () => {
    setSendEnabled(true);
    const status = document.getElementById("status");
    if (status && status.textContent === "Connecting...") {
      status.textContent = "Connected";
    }
  };

  ws.onmessage = (ev) => {
    try { handleServerMessage(JSON.parse(ev.data)); } catch (e) { console.error(e); }
  };

  ws.onclose = () => {
    waiting = false;
    showTyping(false);
    setSendEnabled(false);
  };

  ws.onerror = () => {
    const status = document.getElementById("status");
    if (status) status.textContent = "Connection error";
  };
}

async function sendMessage(text) {
  const trimmed = (text || "").trim();
  if (!trimmed || waiting || !ws || ws.readyState !== WebSocket.OPEN) return;
  appendMessage("user", trimmed);
  waiting = true;
  showTyping(true);
  setSendEnabled(false);
  ws.send(JSON.stringify({ message: trimmed }));
}

async function openSession(id, isNew = false) {
  sessionId = id;
  localStorage.setItem("ati_session_id", sessionId);
  if (ws) ws.close();

  const status = document.getElementById("status");
  if (status) status.textContent = "Connecting...";

  if (!isNew) {
    await loadSessionHistory(sessionId);
  } else {
    clearMessages();
  }

  connectWS();
  await loadSessions();
}

async function newSession() {
  const data = await API.post("/api/user/sessions", {});
  await openSession(data.session_id, true);
}

async function loadSessions() {
  const data = await API.get("/api/user/sessions");
  const list = document.getElementById("sessionList");
  list.innerHTML = "";
  (data.sessions || []).forEach((s) => {
    const item = document.createElement("div");
    item.className = `session-item${s.session_id === sessionId ? " active" : ""}`;
    const label = s.project_type
      ? s.project_type.replace(/_/g, " ")
      : s.stage || "New project";
    item.textContent = label;
    item.title = new Date(s.updated_at).toLocaleString();
    item.onclick = () => openSession(s.session_id, false);
    list.appendChild(item);
  });
}

async function uploadFile(file) {
  if (!sessionId || !file) return;
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`/upload/${sessionId}`, { method: "POST", body: form, credentials: "include" });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Upload failed");
  appendMessage("system", `Uploaded: ${data.filename}`);
  sendMessage(`I uploaded ${data.filename}. ${data.description_preview || ""}`);
}

document.addEventListener("DOMContentLoaded", async () => {
  currentUser = await requireAuth();
  if (!currentUser) return;

  document.getElementById("userName").textContent = currentUser.full_name;
  if (currentUser.role === "admin") {
    document.getElementById("adminLink")?.classList.remove("d-none");
  }

  document.getElementById("newChatBtn")?.addEventListener("click", newSession);
  document.getElementById("logoutBtn")?.addEventListener("click", async () => {
    await API.post("/api/auth/logout", {});
    window.location.href = "/login.html";
  });

  const sendBtn = document.getElementById("sendBtn");
  const input = document.getElementById("messageInput");
  sendBtn?.addEventListener("click", () => { sendMessage(input.value); input.value = ""; });
  input?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input.value); input.value = ""; }
  });
  input?.addEventListener("input", () => setSendEnabled(ws?.readyState === WebSocket.OPEN));

  document.getElementById("fileInput")?.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    if (file) { try { await uploadFile(file); } catch (err) { alert(err.message); } }
    e.target.value = "";
  });

  updateEmptyState();

  sessionId = localStorage.getItem("ati_session_id");
  const sessions = await API.get("/api/user/sessions");
  if (!sessionId && sessions.sessions?.length) {
    sessionId = sessions.sessions[0].session_id;
  }
  if (!sessionId) {
    await newSession();
  } else {
    await openSession(sessionId, false);
  }
});
