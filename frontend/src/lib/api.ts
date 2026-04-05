import axios from "axios";

// In dev, Vite proxies /api → http://127.0.0.1:8000 (see vite.config.ts).
// In prod, VITE_API_BASE_URL points at the Railway deployment.
const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export const api = axios.create({
  baseURL,
  timeout: 30_000,
});

// --- Share key (only used when the backend has SHARED_PASSWORD set) ---
const STORAGE_KEY = "pmo.share_key";

export function getStoredShareKey(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setShareKey(key: string | null): void {
  try {
    if (key) {
      localStorage.setItem(STORAGE_KEY, key);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
    // Update the axios default so every subsequent request carries it.
    if (key) {
      api.defaults.headers.common["X-Share-Key"] = key;
    } else {
      delete api.defaults.headers.common["X-Share-Key"];
    }
  } catch {
    /* ignore */
  }
}

// Re-apply on load so cached keys survive a page refresh
const cached = getStoredShareKey();
if (cached) {
  api.defaults.headers.common["X-Share-Key"] = cached;
}

// Also use the base API URL (no /api/v1 suffix) for the raw fetch() calls
// made by the agent SSE stream. The agent hook builds its own URL, so we
// expose it here for consistency.
export const API_BASE_URL = baseURL;
