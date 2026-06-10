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

document.addEventListener("DOMContentLoaded", async () => {
  const existingUser = typeof getCurrentUserOptional === "function"
    ? await getCurrentUserOptional()
    : null;
  if (existingUser) {
    window.location.href = typeof homePathForUser === "function"
      ? homePathForUser(existingUser)
      : (existingUser.role === "admin" ? "/admin/dashboard.html" : "/chat.html");
    return;
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
        window.location.href = data.user.role === "admin" ? "/admin/dashboard.html" : "/chat.html";
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
        window.location.href = "/chat.html";
      } catch (err) {
        showError(err.message);
      }
    });
  }
});
