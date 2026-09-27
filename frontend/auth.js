document.querySelectorAll(".auth-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".auth-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const target = tab.dataset.tab;
    document.getElementById("loginForm").classList.toggle("hidden", target !== "login");
    document.getElementById("registerForm").classList.toggle("hidden", target !== "register");
  });
});

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;
  const errorEl = document.getElementById("loginError");
  errorEl.textContent = "";

  try {
    await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    window.location.href = "index.html";
  } catch (err) {
    errorEl.textContent = err.message;
  }
});

document.getElementById("registerForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("regName").value.trim();
  const email = document.getElementById("regEmail").value.trim();
  const password = document.getElementById("regPassword").value;
  const errorEl = document.getElementById("registerError");
  errorEl.textContent = "";

  try {
    await apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password, role: "ADMIN" }),
    });
    // auto-login after successful registration
    await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    window.location.href = "index.html";
  } catch (err) {
    errorEl.textContent = err.message;
  }
});
