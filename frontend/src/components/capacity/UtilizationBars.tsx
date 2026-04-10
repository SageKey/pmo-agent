import { motion } from "framer-motion";
import type { RoleUtilization } from "@/types/capacity";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { pct } from "@/lib/format";
import { cn } from "@/lib/cn";

const STATUS_BG: Record<string, string> = {
  BLUE: "bg-sky-500",
  GREEN: "bg-emerald-500",
  YELLOW: "bg-amber-500",
  RED: "bg-red-500",
  GREY: "bg-slate-400",
};
const STATUS_TEXT: Record<string, string> = {
  BLUE: "text-sky-700",
  GREEN: "text-emerald-700",
  YELLOW: "text-amber-700",
  RED: "text-red-700",
  GREY: "text-slate-600",
};

const ROLE_LABEL: Record<string, string> = {
  pm: "Project Manager",
  ba: "Business Analyst",
  functional: "Functional",
  technical: "Technical",
  developer: "Developer",
  infrastructure: "Infrastructure",
  dba: "DBA",
  erp: "ERP",
};

export function UtilizationBars({ roles }: { roles: Record<string, RoleUtilization> }) {
  const entries = Object.values(roles).sort(
    (a, b) => b.utilization_pct - a.utilization_pct,
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Role utilization</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {entries.map((r) => {
          const unstaffed = r.status === "GREY";
          // Unstaffed rows fill the bar to visually signal "all demand, no
          // supply" rather than showing an empty bar that looks like 0%.
          const width = unstaffed
            ? 100
            : Math.min(r.utilization_pct, 1.2) * 100;
          return (
            <div key={r.role_key}>
              <div className="mb-1.5 flex items-center justify-between text-sm">
                <div className="font-medium text-slate-800">
                  {ROLE_LABEL[r.role_key] ?? r.role_key}
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-500 tabular-nums">
                  <span>
                    {r.demand_hrs_week.toFixed(0)} / {r.supply_hrs_week.toFixed(0)} hrs
                  </span>
                  <span className={cn("font-semibold", STATUS_TEXT[r.status])}>
                    {unstaffed ? "Unstaffed" : pct(r.utilization_pct)}
                  </span>
                </div>
              </div>
              <div
                className={cn(
                  "h-2 overflow-hidden rounded-full bg-slate-100",
                  // Diagonal stripe overlay for unstaffed rows to make the
                  // distinction immediately readable without relying on color.
                  unstaffed && "bg-[repeating-linear-gradient(45deg,#e2e8f0_0_6px,#f1f5f9_6px_12px)]",
                )}
              >
                {!unstaffed && (
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${width}%` }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                    className={cn("h-full rounded-full", STATUS_BG[r.status])}
                  />
                )}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
