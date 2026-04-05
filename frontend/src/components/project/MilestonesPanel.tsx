import { motion } from "framer-motion";
import { CheckCircle2, Circle, CircleDashed, Target } from "lucide-react";
import type { Milestone } from "@/types/milestone";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { relativeDate, shortDate } from "@/lib/format";
import { cn } from "@/lib/cn";

const STATUS_META: Record<
  string,
  { icon: React.ReactNode; color: string; label: string }
> = {
  complete: {
    icon: <CheckCircle2 className="h-4 w-4 text-emerald-600" />,
    color: "text-emerald-700",
    label: "Complete",
  },
  in_progress: {
    icon: <CircleDashed className="h-4 w-4 text-navy-600" />,
    color: "text-navy-700",
    label: "In progress",
  },
  not_started: {
    icon: <Circle className="h-4 w-4 text-slate-400" />,
    color: "text-slate-500",
    label: "Not started",
  },
  blocked: {
    icon: <Circle className="h-4 w-4 text-red-500" />,
    color: "text-red-700",
    label: "Blocked",
  },
};

const TYPE_LABEL: Record<string, string> = {
  deliverable: "Deliverable",
  gate: "Gate",
  decision: "Decision",
  review: "Review",
};

const REL_TONE: Record<string, string> = {
  past: "text-red-600",
  soon: "text-amber-600",
  future: "text-slate-500",
  none: "text-slate-400",
};

export function MilestonesPanel({ milestones }: { milestones: Milestone[] }) {
  if (milestones.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Milestones</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center gap-3 py-10 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
              <Target className="h-6 w-6" />
            </div>
            <div className="text-sm font-semibold text-slate-700">No milestones</div>
            <div className="max-w-xs text-xs text-slate-500">
              This project has no milestones defined yet. Add gates, deliverables, or
              decision points to track the plan.
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const complete = milestones.filter((m) => m.status === "complete").length;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Milestones</CardTitle>
          <span className="text-xs tabular-nums text-slate-500">
            {complete} of {milestones.length} complete
          </span>
        </div>
      </CardHeader>
      <CardContent className="pb-2">
        <ol className="relative space-y-0">
          {/* vertical rail */}
          <div
            className="absolute left-[9px] top-2 w-px bg-slate-200"
            style={{ height: `calc(100% - 1rem)` }}
          />
          {milestones.map((m, i) => {
            const meta =
              STATUS_META[m.status ?? "not_started"] ?? STATUS_META.not_started;
            const rel = relativeDate(m.due_date);
            return (
              <motion.li
                key={m.id}
                initial={{ opacity: 0, x: -4 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: i * 0.04 }}
                className="relative flex gap-3 pb-4 last:pb-0"
              >
                <div className="z-10 mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white">
                  {meta.icon}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
                    <span
                      className={cn(
                        "text-sm font-medium",
                        m.status === "complete"
                          ? "text-slate-500 line-through"
                          : "text-slate-900",
                      )}
                    >
                      {m.title}
                    </span>
                    {m.milestone_type && (
                      <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                        {TYPE_LABEL[m.milestone_type] ?? m.milestone_type}
                      </span>
                    )}
                  </div>
                  <div className="mt-0.5 flex flex-wrap items-center gap-x-3 text-[11px] text-slate-500">
                    <span className={meta.color}>{meta.label}</span>
                    {m.due_date && (
                      <span>
                        Due {shortDate(m.due_date)}{" "}
                        <span className={REL_TONE[rel.tone]}>· {rel.label}</span>
                      </span>
                    )}
                    {m.owner && <span>Owner: {m.owner}</span>}
                  </div>
                </div>
              </motion.li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}
