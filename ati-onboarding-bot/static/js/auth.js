document.addEventListener("DOMContentLoaded", () => {
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
        await API.post("/api/auth/register", { email, password, full_name });
        window.location.href = "/chat.html";
      } catch (err) {
        showError(err.message);
      }
    });
  }
});
