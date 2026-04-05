import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Loader2, RefreshCw, XCircle } from "lucide-react";
import { useHealth } from "@/hooks/useHealth";
import { useJiraSync } from "@/hooks/useJira";
import { shortDate } from "@/lib/format";
import { cn } from "@/lib/cn";

export function TopBar({ title, subtitle }: { title: string; subtitle?: string }) {
  const { data } = useHealth();
  const jiraSync = useJiraSync();
  const [flash, setFlash] = useState<{
    tone: "success" | "error";
    message: string;
  } | null>(null);

  const handleSync = async () => {
    try {
      const result = await jiraSync.mutateAsync();
      if (result.error) {
        setFlash({ tone: "error", message: result.error });
      } else if (result.updated > 0) {
        setFlash({
          tone: "success",
          message: `Updated ${result.updated} project${result.updated === 1 ? "" : "s"}`,
        });
      } else {
        setFlash({
          tone: "success",
          message: `In sync · ${result.matched} project${result.matched === 1 ? "" : "s"} checked`,
        });
      }
      setTimeout(() => setFlash(null), 4500);
    } catch (e) {
      const msg = (e as { response?: { data?: { detail?: string } } }).response
        ?.data?.detail ?? (e as Error).message;
      setFlash({ tone: "error", message: msg });
      setTimeout(() => setFlash(null), 6000);
    }
  };

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-8 py-5">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-5 text-xs text-slate-500">
        <AnimatePresence>
          {flash && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className={cn(
                "flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[11px] font-medium ring-1 ring-inset",
                flash.tone === "success"
                  ? "bg-emerald-50 text-emerald-800 ring-emerald-200"
                  : "bg-red-50 text-red-800 ring-red-200",
              )}
            >
              {flash.tone === "success" ? (
                <CheckCircle2 className="h-3 w-3" />
              ) : (
                <XCircle className="h-3 w-3" />
              )}
              {flash.message}
            </motion.div>
          )}
        </AnimatePresence>
        {data && (
          <>
            <div>
              <span className="font-semibold text-slate-700">
                {data.active_project_count}
              </span>{" "}
              active · {data.project_count} total
            </div>
            <div>
              <span className="font-semibold text-slate-700">
                {data.roster_count}
              </span>{" "}
              team members
            </div>
            <div>Data as of {shortDate(data.db_mtime)}</div>
          </>
        )}
        <button
          onClick={handleSync}
          disabled={jiraSync.isPending}
          className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-60"
          title="Pull % complete + health from Jira"
        >
          {jiraSync.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCw className="h-3.5 w-3.5" />
          )}
          Sync Jira
        </button>
      </div>
    </header>
  );
}
