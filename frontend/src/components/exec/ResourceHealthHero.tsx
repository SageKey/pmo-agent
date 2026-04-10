import { motion } from "framer-motion";
import { CheckCircle2, AlertCircle, AlertTriangle, TrendingDown, UserX } from "lucide-react";
import { Link } from "react-router-dom";
import type { RoleUtilization } from "@/types/capacity";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/cn";
import { pct } from "@/lib/format";

const STATUS_DOT: Record<string, string> = {
  BLUE: "bg-sky-500",
  GREEN: "bg-emerald-500",
  YELLOW: "bg-amber-500",
  RED: "bg-red-500",
  GREY: "bg-slate-400",
};
const BAR_BG: Record<string, string> = {
  BLUE: "bg-sky-500",
  GREEN: "bg-emerald-500",
  YELLOW: "bg-amber-500",
  RED: "bg-red-500",
  GREY: "bg-slate-400",
};

const ROLE_LABEL: Record<string, string> = {
  pm: "PM",
  ba: "BA",
  functional: "Functional",
  technical: "Technical",
  developer: "Developer",
  infrastructure: "Infra",
  dba: "DBA",
  erp: "ERP",
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
  const blue = entries.filter((r) => r.status === "BLUE").length;
  const grey = entries.filter((r) => r.status === "GREY").length;
  const green = entries.length - red - yellow - blue - grey;
  const topRole = entries.find((r) => r.status !== "GREY") ?? entries[0];
  const firstUnstaffed = entries.find((r) => r.status === "GREY");

  // Hero banner varies with state.
  // Precedence: RED > GREY (unstaffed) > YELLOW > BLUE > GREEN. Unstaffed
  // outranks YELLOW because "no one to do this" is a bigger org signal
  // than "someone is at 85%" — it forces a hire/reassign decision.
  let banner: {
    icon: React.ReactNode;
    title: string;
    subtitle: string;
    tone: "success" | "warning" | "danger" | "info" | "neutral";
  };
  if (red > 0) {
    banner = {
      icon: <AlertCircle className="h-6 w-6" />,
      title: `${red} role${red === 1 ? "" : "s"} overloaded`,
      subtitle: `${topRole ? `${ROLE_LABEL[topRole.role_key] ?? topRole.role_key} leading at ${pct(topRole.utilization_pct)}` : ""}`,
      tone: "danger",
    };
  } else if (grey > 0) {
    const roleLabel = firstUnstaffed
      ? ROLE_LABEL[firstUnstaffed.role_key] ?? firstUnstaffed.role_key
      : "";
    const hrs = firstUnstaffed?.demand_hrs_week.toFixed(0) ?? "0";
    banner = {
      icon: <UserX className="h-6 w-6" />,
      title: `${grey} role${grey === 1 ? "" : "s"} unstaffed`,
      subtitle: roleLabel
        ? `${roleLabel} has ${hrs} hrs/week of demand with no counted capacity`
        : "Demand exists with nobody assigned to deliver it",
      tone: "neutral",
    };
  } else if (yellow > 0) {
    banner = {
      icon: <AlertTriangle className="h-6 w-6" />,
      title: `${yellow} role${yellow === 1 ? "" : "s"} approaching capacity`,
      subtitle: `${topRole ? `${ROLE_LABEL[topRole.role_key] ?? topRole.role_key} at ${pct(topRole.utilization_pct)}` : ""}`,
      tone: "warning",
    };
  } else if (blue > 0) {
    banner = {
      icon: <TrendingDown className="h-6 w-6" />,
      title: `${blue} role${blue === 1 ? "" : "s"} under-utilized`,
      subtitle: `${green} roles in the ideal band · room to take on more work`,
      tone: "info",
    };
  } else {
    banner = {
      icon: <CheckCircle2 className="h-6 w-6" />,
      title: "All roles in the ideal band",
      subtitle: `${green} roles humming along · healthy utilization across the team`,
      tone: "success",
    };
  }

  const BANNER_TONE = {
    success: "from-emerald-50 to-white ring-emerald-200 text-emerald-800",
    warning: "from-amber-50 to-white ring-amber-200 text-amber-800",
    danger: "from-red-50 to-white ring-red-200 text-red-800",
    info: "from-sky-50 to-white ring-sky-200 text-sky-800",
    neutral: "from-slate-100 to-white ring-slate-300 text-slate-800",
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
            {blue > 0 && <Stat count={blue} label="under" dot="bg-sky-500" />}
            <Stat count={green} label="ideal" dot="bg-emerald-500" />
            <Stat count={yellow} label="stretched" dot="bg-amber-500" />
            <Stat count={red} label="over" dot="bg-red-500" />
            {grey > 0 && <Stat count={grey} label="unstaffed" dot="bg-slate-400" />}
          </div>
        </div>

        <div className="divide-y divide-slate-100">
          {entries.map((r, i) => {
            const unstaffed = r.status === "GREY";
            const width = unstaffed
              ? 100
              : Math.min(r.utilization_pct, 1.25) * 100;
            return (
              <div key={r.role_key} className="flex items-center gap-4 px-6 py-2.5">
                <div className="flex w-32 items-center gap-2 text-sm">
                  <span className={cn("h-2 w-2 rounded-full", STATUS_DOT[r.status])} />
                  <span className="font-medium text-slate-700">
                    {ROLE_LABEL[r.role_key] ?? r.role_key}
                  </span>
                </div>
                <div className="relative flex-1">
                  <div
                    className={cn(
                      "h-2 overflow-hidden rounded-full bg-slate-100",
                      unstaffed &&
                        "bg-[repeating-linear-gradient(45deg,#e2e8f0_0_6px,#f1f5f9_6px_12px)]",
                    )}
                  >
                    {!unstaffed && (
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
                    )}
                  </div>
                </div>
                <div className="w-28 text-right text-xs tabular-nums text-slate-500">
                  {r.demand_hrs_week.toFixed(0)} / {r.supply_hrs_week.toFixed(0)} hrs
                </div>
                <div
                  className={cn(
                    "w-20 text-right text-xs font-semibold tabular-nums",
                    unstaffed ? "text-slate-500" : "text-slate-700",
                  )}
                >
                  {unstaffed ? "Unstaffed" : pct(r.utilization_pct)}
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
