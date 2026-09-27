// Same-origin API base. This frontend is expected to be served
// from the same host/port as the backend (e.g. mounted in FastAPI
// via StaticFiles), so cookies set by /auth/login are sent
// automatically on every request below.
const API_BASE = "http://127.0.0.1:8000/api/v1";

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (res.status === 401) {
    window.location.href = "login.html";
    throw new Error("Not authenticated");
  }

  if (!res.ok) {
    let detail = "Request failed";
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}
