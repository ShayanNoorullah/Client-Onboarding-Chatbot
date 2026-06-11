let streamingBubble = null;
let streamedContent = "";
let currentUser = null;
let sessionId = null;
let ws = null;
let waiting = false;
let consentGiven = false;
let sessionSearchTerm = "";
let sessionSearchTimer = null;

const CONSENT_PHRASE = "i agree";

function sessionStorageKey(userId) {
  return `ati_session_id_${userId}`;
}

function persistSessionId(id) {
  if (!currentUser?.id || !id) return;
  localStorage.setItem(sessionStorageKey(currentUser.id), id);
  localStorage.removeItem("ati_session_id");
}

function clearStoredSessionId() {
  if (typeof clearAuthSession === "function") {
    clearAuthSession(currentUser?.id);
    return;
  }
  if (currentUser?.id) {
    localStorage.removeItem(sessionStorageKey(currentUser.id));
  }
  localStorage.removeItem("ati_session_id");
}

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

function shouldAutoScroll() {
  return typeof getSetting !== "function" || getSetting("autoScroll") !== false;
}

function scrollMessagesToBottom() {
  if (!shouldAutoScroll()) return;
  const container = document.getElementById("messages");
  if (container) container.scrollTop = container.scrollHeight;
}

function appendMessage(role, content) {
  if (!content?.trim()) return;
  const container = document.getElementById("messages");
  const row = document.createElement("div");
  row.className = `msg-row ${role}`;
  row.innerHTML = `<div class="msg-bubble">${linkify(content)}</div>`;
  container.appendChild(row);
  if (typeof animateMessageRow === "function") animateMessageRow(row);
  scrollMessagesToBottom();
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
  if (!el) return;
  const enabled = typeof getSetting === "function" ? getSetting("showTyping") : true;
  el.classList.toggle("d-none", !show || !enabled);
}

function setSendEnabled(enabled) {
  const btn = document.getElementById("sendBtn");
  if (btn) btn.disabled = !enabled || waiting;
}

function renderChips(suggestions) {
  const area = document.getElementById("chips");
  if (!area) return;
  const enabled = typeof getSetting === "function" ? getSetting("showChips") : true;
  area.innerHTML = "";
  if (!enabled) return;
  (suggestions || []).forEach((text) => {
    const chip = document.createElement("button");
    chip.className = "chip";
    chip.textContent = text;
    const fieldMap = { "8 weeks": "timeline", "$10k-$25k": "budget", "Website": "project_type", "Mobile App": "project_type" };
    chip.onclick = () => {
      const field = fieldMap[text];
      if (field && ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: "fill_field", field, value: text }));
        appendMessage("user", text);
      } else sendMessage(text);
    };
    area.appendChild(chip);
  });
}

function updateComposerActionsVisibility() {
  const wrapper = document.getElementById("composerActions");
  const genBtn = document.getElementById("generateBriefBtn");
  const dlWrap = document.getElementById("downloadBriefWrap");
  if (!wrapper) return;
  const showGen = genBtn && !genBtn.classList.contains("d-none");
  const showDl = dlWrap && !dlWrap.classList.contains("d-none");
  wrapper.classList.toggle("d-none", !showGen && !showDl);
}

let briefDownloadBaseUrl = null;

function updateDownloadBtn(data) {
  const wrap = document.getElementById("downloadBriefWrap");
  const btn = document.getElementById("downloadBriefBtn");
  if (!wrap || !btn) return;
  if (data.done && data.brief_download_url) {
    briefDownloadBaseUrl = data.brief_download_url.split("?")[0];
    wrap.classList.remove("d-none");
    const version = data.brief_version > 1 ? ` (v${data.brief_version})` : "";
    btn.textContent = `Download brief${version}`;
  } else {
    briefDownloadBaseUrl = null;
    wrap.classList.add("d-none");
    document.getElementById("downloadBriefMenu")?.classList.add("d-none");
  }
  updateComposerActionsVisibility();
}

function downloadBriefAs(format) {
  if (!briefDownloadBaseUrl) return;
  window.location.href = `${briefDownloadBaseUrl}?format=${format}`;
  document.getElementById("downloadBriefMenu")?.classList.add("d-none");
}

function updateGenerateBriefBtn(data) {
  const btn = document.getElementById("generateBriefBtn");
  if (!btn) return;
  if (data.show_generate_brief && !data.done) {
    btn.classList.remove("d-none");
    btn.disabled = waiting;
  } else {
    btn.classList.add("d-none");
  }
  updateComposerActionsVisibility();
}

function openSidebar() {
  document.getElementById("chatSidebar")?.classList.add("sidebar-drawer-open");
  document.getElementById("sidebarBackdrop")?.classList.add("sidebar-backdrop--visible");
  document.body.classList.add("sidebar-open");
}

function closeSidebar() {
  document.getElementById("chatSidebar")?.classList.remove("sidebar-drawer-open");
  document.getElementById("sidebarBackdrop")?.classList.remove("sidebar-backdrop--visible");
  document.body.classList.remove("sidebar-open");
}

function toggleSidebar() {
  const sidebar = document.getElementById("chatSidebar");
  if (!sidebar) return;
  if (sidebar.classList.contains("sidebar-drawer-open")) {
    closeSidebar();
  } else {
    openSidebar();
  }
}

function isConsentPhrase(text) {
  return (text || "").trim().toLowerCase() === CONSENT_PHRASE;
}

function showConsentError(message) {
  const err = document.getElementById("consentError");
  if (!err) return;
  err.textContent = message || 'Please type exactly "I agree" to continue.';
  err.classList.remove("d-none");
}

function clearConsentError() {
  const err = document.getElementById("consentError");
  if (err) {
    err.textContent = "";
    err.classList.add("d-none");
  }
}

function updateConsentState(data) {
  consentGiven = Boolean(data.consent_given);
  const overlay = document.getElementById("consentOverlay");
  const chatMain = document.querySelector(".chat-main");
  if (!overlay) return;

  if (consentGiven) {
    overlay.classList.add("d-none");
    overlay.setAttribute("aria-hidden", "true");
    chatMain?.classList.remove("consent-blocked");
    clearConsentError();
  } else {
    overlay.classList.remove("d-none");
    overlay.setAttribute("aria-hidden", "false");
    chatMain?.classList.add("consent-blocked");
    setTimeout(() => document.getElementById("consentInput")?.focus(), 50);
  }
  setSendEnabled(ws?.readyState === WebSocket.OPEN && consentGiven && !waiting);
}

async function loadConsentContent() {
  const sectionsEl = document.getElementById("consentSections");
  const contactEl = document.getElementById("consentContact");
  if (!sectionsEl) return;

  try {
    const res = await fetch("/api/public/privacy");
    const data = await res.json();
    const sections = (data.sections || []).slice(0, 4);
    sectionsEl.innerHTML = sections.map((s) => `
      <div class="consent-section-block">
        <h3>${s.title || ""}</h3>
        <p>${(s.body || "").replace(/\n/g, " ")}</p>
      </div>
    `).join("");

    const contact = data.contact || {};
    if (contactEl && (contact.email || contact.phone)) {
      contactEl.innerHTML = [
        contact.email ? `<strong>Email:</strong> ${contact.email}` : "",
        contact.phone ? `<strong>Phone:</strong> ${contact.phone}` : "",
      ].filter(Boolean).join(" · ");
    }
  } catch {
    sectionsEl.innerHTML = `
      <div class="consent-section-block">
        <p>We collect your name, project details, and any files you upload solely to prepare your project brief. We do not sell your data.</p>
      </div>
    `;
  }
}

function syncConsentSubmitState() {
  const input = document.getElementById("consentInput");
  const btn = document.getElementById("consentSubmit");
  if (!input || !btn) return;
  btn.disabled = !isConsentPhrase(input.value);
}

function submitConsent() {
  const input = document.getElementById("consentInput");
  const value = input?.value || "";
  if (!isConsentPhrase(value)) {
    showConsentError('Please type exactly "I agree" to continue.');
    return;
  }
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    showConsentError("Not connected. Please wait and try again.");
    return;
  }
  clearConsentError();
  waiting = true;
  const btn = document.getElementById("consentSubmit");
  if (btn) btn.disabled = true;
  ws.send(JSON.stringify({ action: "consent", agreement: value.trim() }));
}


function updateProgressPanel(data) {
  const panel = document.getElementById("chatProgressPanel");
  const fill = document.getElementById("chatProgressFill");
  const label = document.getElementById("chatProgressLabel");
  if (!panel || !fill || !label) return;
  const score = Math.round((data.readiness_score || 0) * 100);
  const missing = (data.missing_fields || []).slice(0, 3).join(", ");
  if (data.consent_given && !data.done && data.stage !== "consent") {
    panel.classList.remove("d-none");
    fill.style.width = score + "%";
    label.textContent = missing ? `Progress ${score}% — still need: ${missing}` : `Progress ${score}%`;
  } else {
    panel.classList.add("d-none");
  }
}

function showBriefRecap(data) {
  if (!data.show_brief_recap || !data.collected_requirements) return;
  const items = Object.entries(data.collected_requirements).filter(([, v]) => v).map(([k, v]) => `${k}: ${v}`);
  if (!items.length) return;
  appendMessage("assistant", "Here is what I have captured so far:\n" + items.map((i) => "- " + i).join("\n") + "\n\nDoes this look right? Add details or generate your brief when ready.");
}

async function submitBriefFeedback(rating) {
  const briefId = window._lastBriefId;
  if (!briefId) return;
  try {
    await API.post(`/api/briefs/${briefId}/feedback`, { rating, comment: "" });
    document.getElementById("briefFeedback")?.classList.add("d-none");
  } catch (e) {
    console.error(e);
  }
}

function updateStatus(data) {
  const status = document.getElementById("status");
  if (!status) return;
  if (data.auto_summarising) {
    status.textContent = "Generating your brief...";
  } else if (data.done) {
    status.textContent = data.brief_version > 1 ? "Brief updated" : "Brief ready";
  } else if (data.requirements_complete) {
    status.textContent = "Almost ready";
  } else if (data.stage) {
    status.textContent = data.consent_given ? "Gathering requirements" : "Awaiting consent";
  } else {
    status.textContent = "Connected";
  }
}

const CONSENT_PLACEHOLDER = "Welcome! I'm preparing a brief privacy notice";

function handleServerMessage(data) {
  waiting = false;
  showTyping(false);
  setSendEnabled(true);

  if (data.messages?.length) {
    renderHistory(data.messages);
  } else if (data.streamed && streamedContent) {
    if (streamingBubble) streamingBubble.innerHTML = linkify(streamedContent);
    streamingBubble = null;
    streamedContent = "";
  } else if (data.content?.trim()) {
    const container = document.getElementById("messages");
    const rows = container?.querySelectorAll(".msg-row.assistant");
    const last = rows?.[rows.length - 1];
    const lastText = last?.textContent || "";
    if (lastText.includes(CONSENT_PLACEHOLDER) && !data.content.includes(CONSENT_PLACEHOLDER)) {
      last.querySelector(".msg-bubble").innerHTML = linkify(data.content);
      scrollMessagesToBottom();
      updateEmptyState();
    } else {
      appendMessage("assistant", data.content);
    }
  }

  renderChips(data.suggestions);
  updateDownloadBtn(data);
  updateGenerateBriefBtn(data);
  updateStatus(data);
  updateConsentState(data);
  waiting = false;
  syncConsentSubmitState();
  const consentBtn = document.getElementById("consentSubmit");
  if (consentBtn) consentBtn.disabled = !isConsentPhrase(document.getElementById("consentInput")?.value);
}

async function loadSessionHistory(id) {
  try {
    const data = await API.get(`/api/user/sessions/${id}`);
    renderHistory(data.messages);
    updateDownloadBtn(data);
    updateGenerateBriefBtn(data);
    updateStatus(data);
    updateConsentState(data);
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
    try {
      const data = JSON.parse(ev.data);
      if (data.type === "stream_start") {
        streamedContent = "";
        streamingBubble = null;
        return;
      }
      if (data.type === "token") {
        streamedContent += data.content || "";
        if (!streamingBubble) {
          const container = document.getElementById("messages");
          const row = document.createElement("div");
          row.className = "msg-row assistant";
          row.innerHTML = '<div class="msg-bubble streaming-bubble"></div>';
          container.appendChild(row);
          streamingBubble = row.querySelector(".msg-bubble");
          updateEmptyState();
        }
        if (streamingBubble) streamingBubble.textContent = streamedContent;
        scrollMessagesToBottom();
        return;
      }
      if (data.type === "consent_error") {
        waiting = false;
        showConsentError(data.message);
        syncConsentSubmitState();
        return;
      }
      if (data.type === "consent_required") {
        waiting = false;
        updateConsentState(data);
        return;
      }
      handleServerMessage(data);
    } catch (e) {
      console.error(e);
    }
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
  if (!trimmed || waiting || !consentGiven || !ws || ws.readyState !== WebSocket.OPEN) return;
  appendMessage("user", trimmed);
  waiting = true;
  showTyping(true);
  setSendEnabled(false);
  const genBtn = document.getElementById("generateBriefBtn");
  if (genBtn) genBtn.disabled = true;
  ws.send(JSON.stringify({ message: trimmed }));
}

function requestGenerateBrief() {
  if (waiting || !ws || ws.readyState !== WebSocket.OPEN) return;
  waiting = true;
  showTyping(true);
  setSendEnabled(false);
  const genBtn = document.getElementById("generateBriefBtn");
  if (genBtn) genBtn.disabled = true;
  ws.send(JSON.stringify({ action: "generate_brief" }));
}

async function openSession(id, isNew = false) {
  sessionId = id;
  persistSessionId(sessionId);
  if (ws) ws.close();

  const status = document.getElementById("status");
  if (status) status.textContent = "Connecting...";

  if (!isNew) {
    const history = await loadSessionHistory(sessionId);
    if (!history) {
      clearStoredSessionId();
      await newSession();
      return;
    }
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

function getChatDisplayName(session) {
  return session.display_name || "New chat";
}

function sessionsListUrl() {
  const q = sessionSearchTerm.trim();
  return q ? `/api/user/sessions?q=${encodeURIComponent(q)}` : "/api/user/sessions";
}

async function togglePinChat(id, pinned) {
  await API.patch(`/api/user/sessions/${id}`, { pinned: !pinned });
  await loadSessions();
}

async function renameChat(id, currentTitle) {
  const next = window.prompt("Rename chat", currentTitle || "");
  if (next === null) return;
  const title = next.trim();
  if (!title) {
    alert("Chat name cannot be empty.");
    return;
  }
  await API.patch(`/api/user/sessions/${id}`, { title });
  await loadSessions();
}

async function deleteChat(id) {
  if (!confirm("Delete this chat? This cannot be undone.")) return;
  const wasActive = sessionId === id;
  await API.delete(`/api/user/sessions/${id}`);
  if (wasActive) {
    clearStoredSessionId();
    sessionId = null;
    if (ws) ws.close();
    const data = await API.get(sessionsListUrl());
    const remaining = data.sessions || [];
    if (remaining.length > 0) {
      await openSession(remaining[0].session_id, false);
    } else {
      await newSession();
    }
    return;
  }
  await loadSessions();
}

function renderSessionRow(s) {
  const row = document.createElement("div");
  row.className = `session-row${s.session_id === sessionId ? " active" : ""}${s.pinned ? " pinned" : ""}`;
  row.title = new Date(s.updated_at).toLocaleString();

  const label = document.createElement("button");
  label.type = "button";
  label.className = "session-label";
  label.textContent = getChatDisplayName(s);
  label.addEventListener("click", () => {
    closeSidebar();
    openSession(s.session_id, false);
  });

  const actions = document.createElement("div");
  actions.className = "session-actions";

  const pinBtn = document.createElement("button");
  pinBtn.type = "button";
  pinBtn.className = `session-action-btn${s.pinned ? " pinned-active" : ""}`;
  pinBtn.setAttribute("aria-label", s.pinned ? "Unpin chat" : "Pin chat");
  pinBtn.innerHTML = '<svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M9.828.722a.5.5 0 0 1 .354.146l4.95 4.95a.5.5 0 0 1 0 .707c-.48.48-1.072.588-1.503.588-.177 0-.335-.018-.46-.039l-3.134 3.134a5.927 5.927 0 0 1 .16 1.013c.046.702-.032 1.687-.72 2.375a.5.5 0 0 1-.707 0l-2.829-2.828-3.182 3.182c-.195.195-1.219.902-1.414.707s.512-1.22.707-1.414l3.182-3.182-2.828-2.829a.5.5 0 0 1 0-.707c.688-.688 1.673-.766 2.375-.72a5.92 5.92 0 0 1 1.013.16l3.134-3.134a5.96 5.96 0 0 1-.039-.461c0-.43.108-1.022.588-1.503a.5.5 0 0 1 .353-.146z"/></svg>';
  pinBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    togglePinChat(s.session_id, s.pinned).catch((err) => alert(err.message));
  });

  const renameBtn = document.createElement("button");
  renameBtn.type = "button";
  renameBtn.className = "session-action-btn";
  renameBtn.setAttribute("aria-label", "Rename chat");
  renameBtn.innerHTML = '<svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10z"/></svg>';
  renameBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    renameChat(s.session_id, s.title || getChatDisplayName(s)).catch((err) => alert(err.message));
  });

  const deleteBtn = document.createElement("button");
  deleteBtn.type = "button";
  deleteBtn.className = "session-action-btn danger";
  deleteBtn.setAttribute("aria-label", "Delete chat");
  deleteBtn.innerHTML = '<svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3h11V2h-11v1z"/></svg>';
  deleteBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    deleteChat(s.session_id).catch((err) => alert(err.message));
  });

  actions.append(pinBtn, renameBtn, deleteBtn);
  row.append(label, actions);
  return row;
}

async function loadSessions() {
  const data = await API.get(sessionsListUrl());
  const list = document.getElementById("sessionList");
  list.innerHTML = "";
  const sessions = data.sessions || [];
  if (!sessions.length) {
    const empty = document.createElement("div");
    empty.className = "session-empty";
    empty.textContent = sessionSearchTerm.trim() ? "No chats match your search." : "No chats yet.";
    list.appendChild(empty);
    return;
  }
  sessions.forEach((s) => list.appendChild(renderSessionRow(s)));
}

async function uploadFile(file) {
  if (!sessionId || !file) return;
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`/upload/${sessionId}`, { method: "POST", body: form, credentials: "include" });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Upload failed");
  appendMessage("system", `Uploaded: ${data.filename}`);
  if (data.agent_message) appendMessage("assistant", data.agent_message);
  sendMessage(`I uploaded ${data.filename}. ${data.description_preview || ""}`);
}

function isFreshLogin() {
  try {
    if (sessionStorage.getItem("ati_fresh_login") === "1") return true;
  } catch {
    /* ignore */
  }
  return new URLSearchParams(window.location.search).get("fresh") === "1";
}

function clearFreshLoginFlag() {
  try {
    sessionStorage.removeItem("ati_fresh_login");
  } catch {
    /* ignore */
  }
  if (window.location.search.includes("fresh=1")) {
    const url = new URL(window.location.href);
    url.searchParams.delete("fresh");
    window.history.replaceState({}, "", url.pathname + url.search);
  }
}

async function initSessionForUser() {
  if (isFreshLogin()) {
    clearStoredSessionId();
    clearFreshLoginFlag();
    await newSession();
    return;
  }

  const sessionsRes = await API.get("/api/user/sessions");
  const userSessions = sessionsRes.sessions || [];
  const sessionIds = new Set(userSessions.map((s) => s.session_id));

  let storedId = localStorage.getItem(sessionStorageKey(currentUser.id));
  const legacyId = localStorage.getItem("ati_session_id");
  if (legacyId) {
    if (sessionIds.has(legacyId)) {
      storedId = legacyId;
      persistSessionId(legacyId);
    }
    localStorage.removeItem("ati_session_id");
  }

  if (storedId && sessionIds.has(storedId)) {
    await openSession(storedId, false);
    return;
  }

  if (userSessions.length > 0) {
    await openSession(userSessions[0].session_id, false);
    return;
  }

  await newSession();
}

document.addEventListener("DOMContentLoaded", async () => {
  currentUser = await requireAuth();
  if (!currentUser) return;
  if (typeof cacheAuthUser === "function") {
    cacheAuthUser(currentUser);
  }

  document.getElementById("userName").textContent = currentUser.full_name;
  if (currentUser.role === "admin") {
    document.getElementById("adminLink")?.classList.remove("d-none");
  }

  document.getElementById("sidebarToggle")?.addEventListener("click", toggleSidebar);
  document.getElementById("sidebarBackdrop")?.addEventListener("click", closeSidebar);
  document.getElementById("newChatBtn")?.addEventListener("click", () => {
    closeSidebar();
    newSession();
  });
  document.getElementById("sessionSearch")?.addEventListener("input", (e) => {
    sessionSearchTerm = e.target.value;
    clearTimeout(sessionSearchTimer);
    sessionSearchTimer = setTimeout(() => loadSessions().catch(console.error), 200);
  });
  document.getElementById("generateBriefBtn")?.addEventListener("click", requestGenerateBrief);
  document.getElementById("downloadBriefBtn")?.addEventListener("click", (e) => {
    e.stopPropagation();
    const menu = document.getElementById("downloadBriefMenu");
    menu?.classList.toggle("d-none");
  });
  document.querySelectorAll("[data-brief-format]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      downloadBriefAs(btn.dataset.briefFormat);
    });
  });
  document.addEventListener("click", () => {
    document.getElementById("downloadBriefMenu")?.classList.add("d-none");
  });
  document.getElementById("logoutBtn")?.addEventListener("click", async () => {
    if (typeof logoutUser === "function") {
      await logoutUser();
    } else {
      clearStoredSessionId();
      await API.post("/api/auth/logout", {});
    }
    window.location.href = "/login.html";
  });

  const sendBtn = document.getElementById("sendBtn");
  const input = document.getElementById("messageInput");
  sendBtn?.addEventListener("click", () => { sendMessage(input.value); input.value = ""; });
  input?.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" || e.shiftKey) return;
    const sendOnEnter = typeof getSetting === "function" ? getSetting("sendOnEnter") : true;
    if (!sendOnEnter) return;
    e.preventDefault();
    sendMessage(input.value);
    input.value = "";
  });
  input?.addEventListener("input", () => setSendEnabled(ws?.readyState === WebSocket.OPEN));

  document.getElementById("fileInput")?.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    if (file) { try { await uploadFile(file); } catch (err) { alert(err.message); } }
    e.target.value = "";
  });

  document.getElementById("consentInput")?.addEventListener("input", () => {
    clearConsentError();
    syncConsentSubmitState();
  });
  document.getElementById("consentInput")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && isConsentPhrase(e.target.value)) {
      e.preventDefault();
      submitConsent();
    }
  });
  document.getElementById("consentSubmit")?.addEventListener("click", submitConsent);

  await loadConsentContent();
  updateEmptyState();
  await initSessionForUser();
});


document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('[data-rating]').forEach((btn) => {
    btn.addEventListener('click', () => submitBriefFeedback(Number(btn.dataset.rating)));
  });
});
