import { useEffect, useState } from "react";
import { Lock, Loader2 } from "lucide-react";
import { api, getStoredShareKey, setShareKey } from "@/lib/api";
import { useHealth } from "@/hooks/useHealth";

/**
 * Blocks the app with a password modal when the backend reports
 * `auth_required: true` and no valid key is stored locally. On successful
 * entry the key is saved to localStorage and all subsequent axios requests
 * carry an `X-Share-Key` header.
 */
export function ShareKeyGate({ children }: { children: React.ReactNode }) {
  const health = useHealth();
  const [input, setInput] = useState("");
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const authRequired = health.data?.auth_required === true;
  const hasStoredKey = Boolean(getStoredShareKey());

  // While we're still fetching health, render children so the UI shows
  // instantly. The gate only activates when we KNOW auth is required and
  // we have no stored key.
  const needsPrompt = authRequired && !hasStoredKey;

  // 401 interceptor: if any request fails with 401 we clear the key and
  // force the modal back up. Installed once on mount.
  useEffect(() => {
    const id = api.interceptors.response.use(
      (r) => r,
      (err) => {
        if (err?.response?.status === 401) {
          setShareKey(null);
          // Force a re-render by bumping state
          setError("Session expired. Enter the password again.");
          window.setTimeout(() => window.location.reload(), 300);
        }
        return Promise.reject(err);
      },
    );
    return () => api.interceptors.response.eject(id);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setChecking(true);
    setError(null);
    try {
      // Try a lightweight authenticated endpoint (portfolio list) with the
      // provided key. /meta/health is on the public allowlist so we can't
      // use it to verify the key.
      const res = await fetch(`${api.defaults.baseURL}/portfolio/?active_only=true`, {
        headers: { "X-Share-Key": input.trim() },
      });
      if (res.status === 401) {
        setError("Wrong password. Try again.");
        return;
      }
      if (!res.ok) {
        setError(`Unexpected response (${res.status}). Try again.`);
        return;
      }
      setShareKey(input.trim());
      // Reload so every query refetches with the new header
      window.location.reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setChecking(false);
    }
  };

  if (!needsPrompt) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-8 shadow-2xl">
        <div className="mb-5 flex justify-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-navy-500 to-navy-900 text-white shadow-elev">
            <Lock className="h-7 w-7" />
          </div>
        </div>
        <h1 className="text-center text-lg font-semibold tracking-tight text-slate-900">
          ETE IT PMO
        </h1>
        <p className="mt-1 text-center text-xs text-slate-500">
          This instance is password-protected. Enter the shared password to
          continue.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-3">
          <input
            type="password"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Shared password"
            autoFocus
            className="w-full rounded-md border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
          />
          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
              {error}
            </div>
          )}
          <button
            type="submit"
            disabled={checking || !input.trim()}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-navy-900 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-navy-800 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {checking ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Unlock
          </button>
        </form>
      </div>
    </div>
  );
}
