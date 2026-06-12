(function () {
  const V = "3.7.0";

  function ensureToastContainer() {
    let el = document.getElementById("toastContainerAdmin");
    if (!el) {
      el = document.createElement("div");
      el.id = "toastContainerAdmin";
      el.className = "toast-container-admin";
      document.body.appendChild(el);
    }
    return el;
  }

  function showToast(message, type = "success") {
    const container = ensureToastContainer();
    const id = "toast-" + Date.now();
    const bg = type === "error" ? "bg-danger" : type === "warning" ? "bg-warning" : "bg-success";
    const html = `<div id="${id}" class="toast align-items-center text-white ${bg} border-0 mb-2" role="alert">
      <div class="d-flex"><div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div></div>`;
    container.insertAdjacentHTML("beforeend", html);
    const toastEl = document.getElementById(id);
    if (typeof bootstrap !== "undefined" && bootstrap.Toast) {
      const t = new bootstrap.Toast(toastEl, { delay: 4000 });
      t.show();
      toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
    } else {
      setTimeout(() => toastEl.remove(), 4000);
    }
  }

  function showConfirm(message) {
    return new Promise((resolve) => {
      const id = "confirmModal-" + Date.now();
      const html = `<div class="modal fade" id="${id}" tabindex="-1">
        <div class="modal-dialog"><div class="modal-content">
          <div class="modal-header"><h5 class="modal-title">Confirm</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
          <div class="modal-body"><p>${message}</p></div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" data-no>Cancel</button>
            <button type="button" class="btn btn-danger" data-yes>Confirm</button>
          </div></div></div></div>`;
      document.body.insertAdjacentHTML("beforeend", html);
      const modalEl = document.getElementById(id);
      const modal = new bootstrap.Modal(modalEl);
      modalEl.querySelector("[data-yes]").addEventListener("click", () => { modal.hide(); resolve(true); });
      modalEl.querySelector("[data-no]").addEventListener("click", () => resolve(false));
      modalEl.addEventListener("hidden.bs.modal", () => { modalEl.remove(); resolve(false); });
      modal.show();
    });
  }

  function formatDate(isoStr) {
    if (!isoStr) return "—";
    return new Date(isoStr).toLocaleString("en-US", {
      month: "short", day: "numeric", year: "numeric",
      hour: "numeric", minute: "2-digit",
    });
  }

  function getTenantHeader() {
    return localStorage.getItem("coa_admin_tenant") || "";
  }

  function setTenantHeader(tenantId) {
    if (tenantId) localStorage.setItem("coa_admin_tenant", tenantId);
    else localStorage.removeItem("coa_admin_tenant");
  }

  function formatApiError(err) {
    const msg = err?.message || String(err);
    if (msg === "Not Found" || msg.includes("HTTP 404")) {
      return "API route missing — restart the server (uvicorn main:app --reload)";
    }
    if (msg.includes("Permission denied") || msg.includes("HTTP 403")) {
      return msg;
    }
    return msg;
  }

  async function apiRequest(method, url, body) {
    const opts = { method, credentials: "include", headers: {} };
    const tenant = getTenantHeader();
    if (tenant) opts.headers["X-Tenant-ID"] = tenant;
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const err = new Error(data.detail || data.message || `HTTP ${res.status}`);
      err.status = res.status;
      throw err;
    }
    return data;
  }

  const apiGet = (url) => apiRequest("GET", url);
  const apiPost = (url, body) => apiRequest("POST", url, body);
  const apiPut = (url, body) => apiRequest("PUT", url, body);
  const apiPatch = (url, body) => apiRequest("PATCH", url, body);
  const apiDelete = (url) => apiRequest("DELETE", url);

  function renderPagination(container, current, total, pages, onPageChange) {
    if (!container) return;
    const start = total === 0 ? 0 : (current - 1) * 10 + 1;
    const end = Math.min(current * 10, total);
    let btns = "";
    for (let p = 1; p <= pages; p++) {
      btns += `<button class="${p === current ? "active" : ""}" data-page="${p}">${p}</button>`;
    }
    container.innerHTML = `<div class="pagination-admin">
      <span>Showing ${start} to ${end} of ${total} entries</span>
      <div class="page-btns">
        <button data-page="prev" ${current <= 1 ? "disabled" : ""}>Previous</button>
        ${btns}
        <button data-page="next" ${current >= pages ? "disabled" : ""}>Next</button>
      </div></div>`;
    container.querySelectorAll("[data-page]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const v = btn.dataset.page;
        if (v === "prev" && current > 1) onPageChange(current - 1);
        else if (v === "next" && current < pages) onPageChange(current + 1);
        else if (!isNaN(+v)) onPageChange(+v);
      });
    });
  }

  function renderTableControls(container, limit, onLimitChange, onSearch) {
    if (!container) return;
    container.innerHTML = `<div class="data-table-controls">
      <label>Show <select id="entriesSelect">
        ${[10,25,50,100].map((n) => `<option value="${n}" ${n === limit ? "selected" : ""}>${n}</option>`).join("")}
      </select> entries</label>
      <input type="search" id="tableSearch" placeholder="Search..." style="max-width:220px">
    </div>`;
    container.querySelector("#entriesSelect").addEventListener("change", (e) => onLimitChange(+e.target.value));
    let timer;
    container.querySelector("#tableSearch").addEventListener("input", (e) => {
      clearTimeout(timer);
      timer = setTimeout(() => onSearch(e.target.value), 300);
    });
  }

  async function checkAdminAuth() {
    const user = await requireAuth("/login.html");
    if (!user || user.role !== "admin") {
      window.location.href = "/chat.html";
      return null;
    }
    return user;
  }

  function statPulseHtml() {
    const reduceMotion = document.documentElement.getAttribute("data-reduce-motion") === "true";
    if (reduceMotion) return "-";
    return `<span class="stat-pulse" aria-label="Loading"><span class="stat-pulse-dot"></span><span class="stat-pulse-dot"></span><span class="stat-pulse-dot"></span></span>`;
  }

  function setStatLoading(id) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = statPulseHtml();
  }

  function setStatValue(id, value, isHtml = false) {
    const el = document.getElementById(id);
    if (!el) return;
    if (isHtml) el.innerHTML = value;
    else el.textContent = value ?? "-";
  }

  function setStatsLoading(ids) {
    ids.forEach(setStatLoading);
  }

  window.AdminUtils = {
    V: "3.8.4", showToast, showConfirm, formatDate, formatApiError,
    getTenantHeader, setTenantHeader,
    renderPagination, renderTableControls,
    apiGet, apiPost, apiPut, apiPatch, apiDelete,
    checkAdminAuth, statPulseHtml, setStatLoading, setStatValue, setStatsLoading,
  };
})();
