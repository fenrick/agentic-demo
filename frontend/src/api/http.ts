const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";
const token = () => localStorage.getItem("jwt") ?? "";

export async function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  if (!headers.has("Authorization") && token()) {
    headers.set("Authorization", `Bearer ${token()}`);
  }
  if (!headers.has("Content-Type"))
    headers.set("Content-Type", "application/json");
  return fetch(`${API_BASE}${path}`, { ...init, headers });
}
