import { useEffect } from "react";
import { motion } from "framer-motion";
import {
  CalendarCheck,
  Clock,
  AlertOctagon,
  CheckCircle2,
  XCircle,
  Loader2,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/cn";
import { useSchedulePortfolio } from "@/hooks/useScenario";

const ROLE_LABEL: Record<string, string> = {
  pm: "PM",
  ba: "BA",
  functional: "Functional",
  technical: "Technical",
  developer: "Developer",
  infrastructure: "Infrastructure",
  dba: "DBA",
  wms: "WMS",
};

const PRIORITY_BG: Record<string, string> = {
  Highest: "bg-red-100 text-red-700",
  High: "bg-amber-100 text-amber-700",
  Medium: "bg-slate-100 text-slate-700",
  Low: "bg-slate-50 text-slate-500",
};

export function ScheduleView() {
  const schedule = useSchedulePortfolio();

  // Auto-run on mount
  useEffect(() => {
    schedule.mutate({});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const result = schedule.data;
  const loading = schedule.isPending;

  return (
    <div className="space-y-4">
      {/* Run button */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold text-slate-800">
            Capacity-based project scheduling
          </div>
          <p className="mt-0.5 text-xs text-slate-500">
            The engine scans forward through time, placing each plannable
            project at the earliest week where all required roles stay under
            the utilization ceiling. Higher-priority projects get first pick.
          </p>
        </div>
        <Button
          variant="default"
          size="sm"
          onClick={() => schedule.mutate({})}
          disabled={loading}
        >
          {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
          {loading ? "Scheduling…" : "Re-run scheduler"}
        </Button>
      </div>

      {loading && !result && (
        <Card className="flex items-center justify-center py-16 text-sm text-slate-500">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Running capacity-based scheduler…
        </Card>
      )}

      {result && (
        <>
          {/* Summary banner */}
          <SummaryBanner result={result} />

          {/* Bottleneck summary if any */}
          {Object.keys(result.bottleneck_roles).length > 0 && (
            <BottleneckCard bottlenecks={result.bottleneck_roles} />
          )}

          {/* Project list */}
          <Card className="overflow-hidden">
            <div className="border-b border-slate-100 px-5 py-3">
              <div className="text-sm font-semibold text-slate-700">
                Scheduled placement — {result.projects.length} plannable
                project{result.projects.length !== 1 ? "s" : ""}
              </div>
            </div>

            {result.projects.length === 0 ? (
              <div className="px-5 py-12 text-center text-sm text-slate-500">
                No plannable projects found. All projects are either
                in-development, complete, or postponed.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {result.projects.map((p, i) => (
                  <ProjectRow key={p.project_id} project={p} delay={i * 0.04} />
                ))}
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

function SummaryBanner({
  result,
}: {
  result: NonNullable<ReturnType<typeof useSchedulePortfolio>["data"]>;
}) {
  const { can_start_now_count, waiting_count, infeasible_count } = result;

  let tone: string;
  let headline: string;
  let Icon: typeof CheckCircle2;

  if (infeasible_count > 0) {
    tone = "from-amber-50 to-white ring-amber-200 text-amber-800";
    Icon = AlertOctagon;
    headline =
      infeasible_count === result.projects.length
        ? `None of the ${result.projects.length} plannable projects fit within the ${result.horizon_weeks}-week horizon`
        : `${infeasible_count} project${infeasible_count > 1 ? "s" : ""} can't be scheduled in the next ${result.horizon_weeks} weeks`;
  } else if (can_start_now_count === result.projects.length) {
    tone = "from-emerald-50 to-white ring-emerald-200 text-emerald-800";
    Icon = CheckCircle2;
    headline = `All ${can_start_now_count} plannable projects can start immediately — team has capacity`;
  } else if (can_start_now_count > 0) {
    tone = "from-sky-50 to-white ring-sky-200 text-sky-800";
    Icon = CalendarCheck;
    headline = `${can_start_now_count} can start now · ${waiting_count} queued behind capacity constraints`;
  } else {
    tone = "from-slate-100 to-white ring-slate-300 text-slate-800";
    Icon = Clock;
    headline = `All ${waiting_count} projects are queued — earliest slot opens soon`;
  }

  const subtitle = `Utilization ceiling: ${Math.round(result.max_util_pct * 100)}% · Horizon: ${result.horizon_weeks} weeks`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
    >
      <Card className="overflow-hidden ring-1 ring-inset ring-slate-200">
        <div
          className={cn(
            "flex items-start gap-4 bg-gradient-to-r px-6 py-5 ring-1 ring-inset",
            tone,
          )}
        >
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/70 ring-1 ring-inset ring-white">
            <Icon className="h-6 w-6" />
          </div>
          <div>
            <div className="text-lg font-semibold tracking-tight">
              {headline}
            </div>
            <div className="mt-0.5 text-sm opacity-80">{subtitle}</div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

function BottleneckCard({
  bottlenecks,
}: {
  bottlenecks: Record<string, number>;
}) {
  const entries = Object.entries(bottlenecks).sort((a, b) => b[1] - a[1]);
  return (
    <Card className="px-5 py-4">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
        Bottleneck roles
      </div>
      <div className="flex flex-wrap gap-3">
        {entries.map(([role, count]) => (
          <div
            key={role}
            className="flex items-center gap-2 rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-200"
          >
            <AlertOctagon className="h-3 w-3" />
            {ROLE_LABEL[role] ?? role} blocking {count} project
            {count !== 1 ? "s" : ""}
          </div>
        ))}
      </div>
    </Card>
  );
}

function ProjectRow({
  project: p,
  delay,
}: {
  project: NonNullable<
    ReturnType<typeof useSchedulePortfolio>["data"]
  >["projects"][0];
  delay: number;
}) {
  const feasible = p.suggested_start !== null;

  return (
    <motion.div
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.25, delay }}
      className={cn(
        "grid grid-cols-12 items-center gap-4 px-5 py-3",
        !feasible && "bg-red-50/40",
      )}
    >
      {/* Project name + priority chip */}
      <div className="col-span-4">
        <div className="text-sm font-semibold text-slate-800">{p.project_name}</div>
        <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-500">
          <span className="font-mono">{p.project_id}</span>
          <span
            className={cn(
              "rounded-full px-2 py-0.5 text-[10px] font-semibold",
              PRIORITY_BG[p.priority] ?? PRIORITY_BG.Medium,
            )}
          >
            {p.priority}
          </span>
          <span>{p.est_hours}h</span>
        </div>
      </div>

      {/* Suggested dates or infeasible */}
      <div className="col-span-3 text-sm">
        {feasible ? (
          <div className="space-y-0.5">
            <div className="flex items-center gap-1.5">
              {p.can_start_now ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              ) : (
                <Clock className="h-3.5 w-3.5 text-sky-500" />
              )}
              <span className="font-medium text-slate-800">
                {p.suggested_start}
              </span>
            </div>
            <div className="text-xs text-slate-500">
              → {p.suggested_end} ({p.duration_weeks.toFixed(0)}w)
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-red-600">
            <XCircle className="h-3.5 w-3.5" />
            <span className="text-xs font-medium">
              Can't schedule in horizon
            </span>
          </div>
        )}
      </div>

      {/* Wait weeks */}
      <div className="col-span-2 text-center">
        {feasible && p.wait_weeks !== null ? (
          <div>
            <div className="text-sm font-semibold tabular-nums text-slate-800">
              {p.wait_weeks === 0 ? "Now" : `${p.wait_weeks}w`}
            </div>
            <div className="text-[10px] uppercase tracking-wider text-slate-400">
              {p.wait_weeks === 0 ? "ready" : "wait"}
            </div>
          </div>
        ) : (
          <span className="text-xs text-slate-400">—</span>
        )}
      </div>

      {/* Bottleneck */}
      <div className="col-span-3 text-right">
        {p.bottleneck_role && !p.can_start_now ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-0.5 text-[11px] font-medium text-red-700 ring-1 ring-inset ring-red-200">
            <AlertOctagon className="h-3 w-3" />
            {ROLE_LABEL[p.bottleneck_role] ?? p.bottleneck_role}
          </span>
        ) : p.can_start_now ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-medium text-emerald-700 ring-1 ring-inset ring-emerald-200">
            <CheckCircle2 className="h-3 w-3" />
            Ready
          </span>
        ) : null}
      </div>
    </motion.div>
  );
}
