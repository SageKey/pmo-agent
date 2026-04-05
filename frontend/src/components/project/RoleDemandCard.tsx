import { motion } from "framer-motion";
import type { ProjectDemand } from "@/types/projectDemand";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/cn";

const ROLE_LABEL: Record<string, string> = {
  pm: "Project Manager",
  ba: "Business Analyst",
  functional: "Functional",
  technical: "Technical",
  developer: "Developer",
  infrastructure: "Infrastructure",
  dba: "DBA",
  wms: "WMS",
};

const PHASE_COLORS: Record<string, string> = {
  discovery: "bg-sky-200",
  planning: "bg-indigo-200",
  design: "bg-violet-200",
  build: "bg-emerald-300",
  test: "bg-amber-200",
  deploy: "bg-rose-200",
};

export function RoleDemandCard({ demand }: { demand: ProjectDemand }) {
  // Sort roles by average weekly demand descending (drop zero-alloc roles)
  const active = demand.roles
    .filter((r) => r.role_alloc_pct > 0)
    .sort((a, b) => b.weekly_hours - a.weekly_hours);

  if (active.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Role allocation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="py-6 text-center text-sm text-slate-500">
            No role allocations set for this project yet.
          </div>
        </CardContent>
      </Card>
    );
  }

  const maxHrs = Math.max(...active.map((r) => r.weekly_hours));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Role demand · average weekly hours by phase</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {active.map((role, i) => {
            const widthPct = maxHrs > 0 ? (role.weekly_hours / maxHrs) * 100 : 0;
            return (
              <motion.div
                key={role.role_key}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: i * 0.05 }}
              >
                <div className="mb-1.5 flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-800">
                      {ROLE_LABEL[role.role_key] ?? role.role_key}
                    </span>
                    <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-slate-600">
                      {(role.role_alloc_pct * 100).toFixed(0)}% alloc
                    </span>
                  </div>
                  <span className="text-xs font-semibold tabular-nums text-slate-700">
                    {role.weekly_hours.toFixed(1)} hrs/wk
                  </span>
                </div>

                <div
                  className="relative h-3 overflow-hidden rounded-full bg-slate-100"
                  style={{ width: `${Math.max(widthPct, 10)}%` }}
                >
                  {/* Phase composition bar — segments are weighted per phase */}
                  <PhaseSegments phases={role.phase_breakdown} />
                </div>

                <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-slate-500">
                  {role.phase_breakdown
                    .filter((p) => p.weekly_hours > 0)
                    .sort((a, b) => b.weekly_hours - a.weekly_hours)
                    .slice(0, 6)
                    .map((p) => (
                      <span key={p.phase}>
                        <span
                          className={cn(
                            "mr-1 inline-block h-1.5 w-1.5 rounded-full align-middle",
                            PHASE_COLORS[p.phase] ?? "bg-slate-300",
                          )}
                        />
                        {p.phase} {p.weekly_hours.toFixed(1)}h
                      </span>
                    ))}
                </div>
              </motion.div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

function PhaseSegments({
  phases,
}: {
  phases: { phase: string; weekly_hours: number }[];
}) {
  const total = phases.reduce((s, p) => s + p.weekly_hours, 0);
  if (total <= 0) {
    return <div className="h-full w-full bg-slate-300" />;
  }
  return (
    <div className="flex h-full w-full">
      {phases
        .filter((p) => p.weekly_hours > 0)
        .map((p) => (
          <motion.div
            key={p.phase}
            initial={{ width: 0 }}
            animate={{ width: `${(p.weekly_hours / total) * 100}%` }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className={cn("h-full", PHASE_COLORS[p.phase] ?? "bg-slate-400")}
            title={`${p.phase}: ${p.weekly_hours.toFixed(1)} hrs/wk`}
          />
        ))}
    </div>
  );
}
