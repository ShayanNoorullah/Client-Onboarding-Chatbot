function initPasswordToggles() {
  document.querySelectorAll(".password-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = document.getElementById(btn.dataset.target);
      if (!input) return;
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.querySelector(".eye-open")?.classList.toggle("d-none", show);
      btn.querySelector(".eye-closed")?.classList.toggle("d-none", !show);
      btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
      input.focus();
    });
  });
}

function showExistingSessionBanner(user) {
  const banner = document.getElementById("authSessionBanner");
  if (!banner || !user) return;
  const dest = typeof homePathForUser === "function"
    ? homePathForUser(user)
    : (user.role === "admin" ? "/admin/dashboard.html" : "/chat.html");
  const label = user.role === "admin" ? "Admin dashboard" : "Chat";
  banner.innerHTML = `
    <p class="mb-2">Signed in as <strong>${user.full_name || user.email}</strong>.</p>
    <div class="d-flex gap-2 flex-wrap justify-content-center">
      <a href="${dest}" class="btn-primary-custom" style="display:inline-block;padding:8px 16px;text-decoration:none;">Continue to ${label}</a>
      <button type="button" class="btn-secondary-custom" id="authSignOutBtn" style="padding:8px 16px;">Sign out</button>
    </div>`;
  banner.classList.remove("d-none");
  document.getElementById("authSignOutBtn")?.addEventListener("click", async () => {
    if (typeof logoutUser === "function") await logoutUser();
    window.location.reload();
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  const params = new URLSearchParams(window.location.search);

  if (params.get("logout") === "1" && typeof logoutUser === "function") {
    await logoutUser();
    window.history.replaceState({}, "", window.location.pathname);
  }

  const existingUser = typeof fetchSessionUser === "function"
    ? await fetchSessionUser()
    : null;

  if (existingUser && !params.get("logout")) {
    showExistingSessionBanner(existingUser);
  }

  initPasswordToggles();

  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");
  const googleBtn = document.getElementById("googleLogin");
  const errEl = document.getElementById("authError");

  function showError(msg) {
    if (errEl) { errEl.textContent = msg; errEl.classList.remove("d-none"); }
  }

  if (googleBtn) {
    googleBtn.addEventListener("click", () => {
      window.location.href = "/api/auth/google/login";
    });
  }

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;
      try {
        const data = await API.post("/api/auth/login", { email, password });
        if (typeof cacheAuthUser === "function") cacheAuthUser(data.user);
        try {
          sessionStorage.setItem("ati_fresh_login", "1");
        } catch {
          /* ignore */
        }
        window.location.replace(
          data.user.role === "admin" ? "/admin/dashboard.html" : "/chat.html"
        );
      } catch (err) {
        showError(err.message);
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const full_name = document.getElementById("fullName").value;
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;
      try {
        const data = await API.post("/api/auth/register", { email, password, full_name });
        if (typeof cacheAuthUser === "function") cacheAuthUser(data.user);
        try {
          sessionStorage.setItem("ati_fresh_login", "1");
        } catch {
          /* ignore */
        }
        window.location.replace("/chat.html");
      } catch (err) {
        showError(err.message);
      }
    });
  }
});
