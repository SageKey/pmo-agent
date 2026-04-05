import { motion } from "framer-motion";
import {
  ArrowUpRight,
  Camera,
  History,
  Loader2,
  Plus,
  TrendingUp,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  useCreateSnapshot,
  useDetectChanges,
  useLatestSnapshot,
} from "@/hooks/useSnapshots";
import { cn } from "@/lib/cn";

function formatRelative(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const diffHrs = (Date.now() - d.getTime()) / 3_600_000;
  if (diffHrs < 1) return "just now";
  if (diffHrs < 24) return `${Math.round(diffHrs)}h ago`;
  const diffDays = Math.round(diffHrs / 24);
  if (diffDays < 14) return `${diffDays}d ago`;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function ChangesCard({ delay = 0 }: { delay?: number }) {
  const latest = useLatestSnapshot();
  const changes = useDetectChanges();
  const createMutation = useCreateSnapshot();

  const handleSaveSnapshot = async () => {
    try {
      await createMutation.mutateAsync("");
    } catch {
      /* error surfaces via mutation.error */
    }
  };

  const c = changes.data;
  const totalChanges = c
    ? c.new_projects.length +
      c.removed_projects.length +
      c.status_changes.length +
      c.progress_changes.length +
      c.date_changes.length +
      c.priority_changes.length +
      c.hours_changes.length
    : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay }}
    >
      <Card className="ring-1 ring-inset ring-slate-200">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>What changed since last snapshot</CardTitle>
            <div className="flex items-center gap-2">
              {latest.data && (
                <span className="text-[11px] text-slate-500">
                  Last snapshot: {formatRelative(latest.data.taken_at)}
                </span>
              )}
              <Button
                size="sm"
                variant="outline"
                onClick={handleSaveSnapshot}
                disabled={createMutation.isPending}
              >
                {createMutation.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Camera className="h-3.5 w-3.5" />
                )}
                Save snapshot
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {changes.isLoading && (
            <div className="py-6 text-center text-sm text-slate-500">
              Computing changes…
            </div>
          )}

          {c && !c.has_previous && (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                <History className="h-6 w-6" />
              </div>
              <div className="text-sm font-semibold text-slate-700">
                No snapshot yet
              </div>
              <div className="max-w-sm text-xs text-slate-500">
                Click "Save snapshot" to record the current state. Next time you
                come back, this card will show everything that changed.
              </div>
            </div>
          )}

          {c && c.has_previous && totalChanges === 0 && (
            <div className="flex items-center gap-3 rounded-lg bg-emerald-50 px-4 py-3 text-sm ring-1 ring-inset ring-emerald-200">
              <TrendingUp className="h-4 w-4 text-emerald-700" />
              <span className="text-emerald-900">
                No changes since last snapshot. You're up to date.
              </span>
            </div>
          )}

          {c && c.has_previous && totalChanges > 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-3 text-xs text-slate-600">
                <strong className="text-slate-900">{totalChanges}</strong>{" "}
                change{totalChanges === 1 ? "" : "s"} across{" "}
                {
                  [
                    c.new_projects.length && "new",
                    c.removed_projects.length && "removed",
                    c.status_changes.length && "status",
                    c.progress_changes.length && "progress",
                    c.date_changes.length && "dates",
                    c.priority_changes.length && "priority",
                    c.hours_changes.length && "hours",
                  ]
                    .filter(Boolean)
                    .join(" · ")
                }
              </div>

              <Section
                title="New projects"
                items={c.new_projects}
                tone="emerald"
                icon={<Plus className="h-3 w-3" />}
                renderLabel={(e) => `${e.project_id} · ${e.project_name}`}
              />
              <Section
                title="Status changes"
                items={c.status_changes}
                tone="amber"
                renderLabel={(e) =>
                  `${e.project_id} · ${e.old_value ?? "—"} → ${e.new_value ?? "—"}`
                }
              />
              <Section
                title="Progress updates"
                items={c.progress_changes}
                tone="sky"
                renderLabel={(e) =>
                  `${e.project_id} · ${Math.round((e.old_value as number ?? 0) * 100)}% → ${Math.round((e.new_value as number ?? 0) * 100)}%`
                }
              />
              <Section
                title="Priority changes"
                items={c.priority_changes}
                tone="violet"
                renderLabel={(e) =>
                  `${e.project_id} · ${e.old_value ?? "—"} → ${e.new_value ?? "—"}`
                }
              />
              <Section
                title="Date changes"
                items={c.date_changes}
                tone="slate"
                renderLabel={(e) =>
                  `${e.project_id} · ${e.field ?? "date"}: ${e.old_value ?? "—"} → ${e.new_value ?? "—"}`
                }
              />
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

const TONE_STYLES: Record<string, string> = {
  emerald: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  amber: "bg-amber-50 text-amber-800 ring-amber-200",
  sky: "bg-sky-50 text-sky-800 ring-sky-200",
  violet: "bg-violet-50 text-violet-800 ring-violet-200",
  slate: "bg-slate-50 text-slate-700 ring-slate-200",
};

function Section({
  title,
  items,
  tone,
  icon,
  renderLabel,
}: {
  title: string;
  items: Array<Record<string, unknown>>;
  tone: string;
  icon?: React.ReactNode;
  renderLabel: (item: Record<string, unknown>) => string;
}) {
  if (items.length === 0) return null;
  return (
    <div>
      <div className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
        {icon}
        {title}
        <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold tabular-nums text-slate-600">
          {items.length}
        </span>
      </div>
      <ul className="space-y-1">
        {items.slice(0, 6).map((item, i) => {
          const pid = item.project_id as string | undefined;
          return (
            <li
              key={i}
              className={cn(
                "flex items-center justify-between gap-2 rounded-md px-2.5 py-1.5 text-xs ring-1 ring-inset",
                TONE_STYLES[tone],
              )}
            >
              <span className="truncate">{renderLabel(item)}</span>
              {pid && (
                <Link
                  to={`/portfolio/${pid}`}
                  className="shrink-0 opacity-60 hover:opacity-100"
                >
                  <ArrowUpRight className="h-3 w-3" />
                </Link>
              )}
            </li>
          );
        })}
        {items.length > 6 && (
          <li className="text-[11px] text-slate-500">
            + {items.length - 6} more
          </li>
        )}
      </ul>
    </div>
  );
}
