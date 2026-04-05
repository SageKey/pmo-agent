import axios from "axios";

// In dev, Vite proxies /api → http://127.0.0.1:8000 (see vite.config.ts).
// In prod, VITE_API_BASE_URL points at the Railway deployment.
const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export const api = axios.create({
  baseURL,
  timeout: 30_000,
});
