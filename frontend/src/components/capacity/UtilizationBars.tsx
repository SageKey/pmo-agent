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
};
const STATUS_TEXT: Record<string, string> = {
  BLUE: "text-sky-700",
  GREEN: "text-emerald-700",
  YELLOW: "text-amber-700",
  RED: "text-red-700",
};

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
          const width = Math.min(r.utilization_pct, 1.2) * 100;
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
                    {pct(r.utilization_pct)}
                  </span>
                </div>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${width}%` }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                  className={cn("h-full rounded-full", STATUS_BG[r.status])}
                />
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
