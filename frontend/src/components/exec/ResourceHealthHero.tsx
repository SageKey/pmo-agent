import { motion } from "framer-motion";
import { CheckCircle2, AlertCircle, AlertTriangle } from "lucide-react";
import { Link } from "react-router-dom";
import type { RoleUtilization } from "@/types/capacity";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/cn";
import { pct } from "@/lib/format";

const STATUS_DOT: Record<string, string> = {
  GREEN: "bg-emerald-500",
  YELLOW: "bg-amber-500",
  RED: "bg-red-500",
};
const BAR_BG: Record<string, string> = {
  GREEN: "bg-emerald-500",
  YELLOW: "bg-amber-500",
  RED: "bg-red-500",
};

const ROLE_LABEL: Record<string, string> = {
  pm: "PM",
  ba: "BA",
  functional: "Functional",
  technical: "Technical",
  developer: "Developer",
  infrastructure: "Infra",
  dba: "DBA",
  wms: "WMS",
};

export function ResourceHealthHero({
  roles,
  delay = 0,
}: {
  roles: Record<string, RoleUtilization>;
  delay?: number;
}) {
  const entries = Object.values(roles).sort(
    (a, b) => b.utilization_pct - a.utilization_pct,
  );

  const red = entries.filter((r) => r.status === "RED").length;
  const yellow = entries.filter((r) => r.status === "YELLOW").length;
  const green = entries.length - red - yellow;
  const topRole = entries[0];

  // Hero banner varies with state — success, warning, or alert.
  let banner: {
    icon: React.ReactNode;
    title: string;
    subtitle: string;
    tone: "success" | "warning" | "danger";
  };
  if (red > 0) {
    banner = {
      icon: <AlertCircle className="h-6 w-6" />,
      title: `${red} role${red === 1 ? "" : "s"} overloaded`,
      subtitle: `${topRole ? `${ROLE_LABEL[topRole.role_key] ?? topRole.role_key} leading at ${pct(topRole.utilization_pct)}` : ""}`,
      tone: "danger",
    };
  } else if (yellow > 0) {
    banner = {
      icon: <AlertTriangle className="h-6 w-6" />,
      title: `${yellow} role${yellow === 1 ? "" : "s"} approaching capacity`,
      subtitle: `${topRole ? `${ROLE_LABEL[topRole.role_key] ?? topRole.role_key} at ${pct(topRole.utilization_pct)}` : ""}`,
      tone: "warning",
    };
  } else {
    banner = {
      icon: <CheckCircle2 className="h-6 w-6" />,
      title: "All roles green — ready for new work",
      subtitle: `${green} roles under 80% · headroom across the team`,
      tone: "success",
    };
  }

  const BANNER_TONE = {
    success: "from-emerald-50 to-white ring-emerald-200 text-emerald-800",
    warning: "from-amber-50 to-white ring-amber-200 text-amber-800",
    danger: "from-red-50 to-white ring-red-200 text-red-800",
  }[banner.tone];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: "easeOut" }}
    >
      <Card className="overflow-hidden ring-1 ring-inset ring-slate-200">
        <div
          className={cn(
            "flex items-center gap-4 bg-gradient-to-r px-6 py-5 ring-1 ring-inset",
            BANNER_TONE,
          )}
        >
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/70 ring-1 ring-inset ring-white">
            {banner.icon}
          </div>
          <div className="min-w-0">
            <div className="text-lg font-semibold tracking-tight">{banner.title}</div>
            {banner.subtitle && (
              <div className="mt-0.5 text-sm opacity-80">{banner.subtitle}</div>
            )}
          </div>
          <div className="ml-auto hidden items-center gap-4 md:flex">
            <Stat count={green} label="green" dot="bg-emerald-500" />
            <Stat count={yellow} label="yellow" dot="bg-amber-500" />
            <Stat count={red} label="red" dot="bg-red-500" />
          </div>
        </div>

        <div className="divide-y divide-slate-100">
          {entries.map((r, i) => {
            const width = Math.min(r.utilization_pct, 1.25) * 100;
            return (
              <div key={r.role_key} className="flex items-center gap-4 px-6 py-2.5">
                <div className="flex w-32 items-center gap-2 text-sm">
                  <span className={cn("h-2 w-2 rounded-full", STATUS_DOT[r.status])} />
                  <span className="font-medium text-slate-700">
                    {ROLE_LABEL[r.role_key] ?? r.role_key}
                  </span>
                </div>
                <div className="relative flex-1">
                  <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${width}%` }}
                      transition={{
                        duration: 0.6,
                        delay: delay + 0.15 + i * 0.04,
                        ease: "easeOut",
                      }}
                      className={cn("h-full rounded-full", BAR_BG[r.status])}
                    />
                  </div>
                </div>
                <div className="w-28 text-right text-xs tabular-nums text-slate-500">
                  {r.demand_hrs_week.toFixed(0)} / {r.supply_hrs_week.toFixed(0)} hrs
                </div>
                <div className="w-12 text-right text-sm font-semibold tabular-nums text-slate-700">
                  {pct(r.utilization_pct)}
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex items-center justify-end border-t border-slate-100 bg-slate-50 px-6 py-2.5 text-xs">
          <Link
            to="/capacity"
            className="font-medium text-navy-700 hover:text-navy-900"
          >
            Open capacity view →
          </Link>
        </div>
      </Card>
    </motion.div>
  );
}

function Stat({
  count,
  label,
  dot,
}: {
  count: number;
  label: string;
  dot: string;
}) {
  return (
    <div className="flex items-center gap-1.5 text-xs font-medium text-slate-600">
      <span className={cn("h-2 w-2 rounded-full", dot)} />
      <span className="tabular-nums text-slate-900">{count}</span>
      <span>{label}</span>
    </div>
  );
}
