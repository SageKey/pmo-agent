import { motion } from "framer-motion";
import { FolderKanban, Users, Activity, Check, AlertTriangle } from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { Card } from "@/components/ui/card";
import { useHealth } from "@/hooks/useHealth";
import { useUtilization } from "@/hooks/useCapacity";
import { usePortfolio } from "@/hooks/usePortfolio";
import { KpiCard } from "@/components/exec/KpiCard";
import { ResourceHealthHero } from "@/components/exec/ResourceHealthHero";
import { PriorityProjectRow } from "@/components/exec/PriorityProjectRow";
import { ChangesCard } from "@/components/exec/ChangesCard";

const ROLE_LABEL: Record<string, string> = {
  pm: "PM",
  ba: "BA",
  functional: "Functional",
  technical: "Technical",
  developer: "Developer",
  infrastructure: "Infrastructure",
  dba: "DBA",
  erp: "ERP",
};

const PRIORITY_ORDER: Record<string, number> = {
  Highest: 0,
  High: 1,
  Medium: 2,
  Low: 3,
};

export function ExecutiveSummary() {
  const health = useHealth();
  const util = useUtilization();
  const portfolio = usePortfolio(true);

  const roles = util.data?.roles ?? {};
  const utilEntries = Object.values(roles);
  const red = utilEntries.filter((r) => r.status === "RED").length;
  const yellow = utilEntries.filter((r) => r.status === "YELLOW").length;
  const blue = utilEntries.filter((r) => r.status === "BLUE").length;
  const grey = utilEntries.filter((r) => r.status === "GREY").length;

  // Weighted utilization across the whole team — total demand divided by
  // total supply. This is the metric that actually moves when someone is
  // excluded from capacity (supply drops, ratio rises). A simple average
  // across the 8 roles gives ERP (14 hrs) the same weight as Developer
  // (80 hrs), which masks real capacity shifts.
  const totalDemand = utilEntries.reduce((s, r) => s + r.demand_hrs_week, 0);
  const totalSupply = utilEntries.reduce((s, r) => s + r.supply_hrs_week, 0);
  const avgUtil = totalSupply > 0 ? totalDemand / totalSupply : 0;

  // Peak role (for subtitle context) — shows WHICH role is running hottest
  // so the headline number has a "caused by" story.
  const peakRole = utilEntries
    .slice()
    .sort((a, b) => b.utilization_pct - a.utilization_pct)[0];

  const activeCount = health.data?.active_project_count ?? 0;
  const totalCount = health.data?.project_count ?? 0;
  const headcount = health.data?.roster_count ?? 0;

  // Active share: what fraction of the portfolio is currently in-flight
  const activeShare = totalCount > 0 ? activeCount / totalCount : 0;

  // "At risk" combined count — unstaffed roles count as at-risk because
  // they signal a real gap that needs attention (hire, reassign, or zero
  // out stale allocations).
  const atRisk = red + yellow + grey;
  const riskTone: "success" | "warning" | "danger" =
    red > 0 ? "danger" : yellow > 0 || grey > 0 ? "warning" : "success";

  const utilTone: "success" | "warning" | "danger" =
    avgUtil >= 1 ? "danger" : avgUtil >= 0.8 ? "warning" : "success";

  const topProjects = (portfolio.data ?? [])
    .slice()
    .sort((a, b) => {
      const pa = PRIORITY_ORDER[a.priority ?? "Low"] ?? 99;
      const pb = PRIORITY_ORDER[b.priority ?? "Low"] ?? 99;
      if (pa !== pb) return pa - pb;
      return (b.est_hours ?? 0) - (a.est_hours ?? 0);
    })
    .filter((p) => p.priority === "Highest" || p.priority === "High")
    .slice(0, 8);

  return (
    <>
      <TopBar title="Executive Summary" subtitle="Board-ready portfolio snapshot." />
      <div className="space-y-6 p-8">
        {/* KPI row */}
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            label="Active projects"
            value={activeCount}
            subvalue={`of ${totalCount} total · ${Math.round(activeShare * 100)}% in-flight`}
            icon={<FolderKanban className="h-4 w-4" />}
            tone="neutral"
            delay={0.0}
          />
          <KpiCard
            label="Team headcount"
            value={headcount}
            subvalue="across 8 IT roles"
            icon={<Users className="h-4 w-4" />}
            tone="neutral"
            delay={0.05}
          />
          <KpiCard
            label="Team utilization"
            value={`${Math.round(avgUtil * 100)}%`}
            subvalue={
              peakRole
                ? `Peak: ${ROLE_LABEL[peakRole.role_key] ?? peakRole.role_key} at ${Math.round(peakRole.utilization_pct * 100)}%`
                : utilTone === "success"
                  ? "Comfortable — room to take on work"
                  : utilTone === "warning"
                    ? "Approaching capacity"
                    : "Over capacity — action needed"
            }
            icon={<Activity className="h-4 w-4" />}
            tone={utilTone}
            delay={0.1}
          />
          <KpiCard
            label="Roles at risk"
            value={atRisk}
            subvalue={
              atRisk === 0
                ? blue > 0
                  ? `${blue} under-utilized · no overloads`
                  : "All clear · no bottlenecks"
                : grey > 0 && red === 0 && yellow === 0
                  ? `${grey} unstaffed · needs hire or reassign`
                  : `${red} over · ${yellow} approaching${grey > 0 ? ` · ${grey} unstaffed` : ""}`
            }
            icon={
              atRisk === 0 ? (
                <Check className="h-4 w-4" />
              ) : (
                <AlertTriangle className="h-4 w-4" />
              )
            }
            tone={riskTone}
            delay={0.15}
          />
        </div>

        {/* Hero: Resource health at a glance */}
        {util.data && <ResourceHealthHero roles={roles} delay={0.2} />}

        {/* What changed since last snapshot */}
        <ChangesCard delay={0.22} />

        {/* Top-priority projects list */}
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.25 }}
        >
          <Card className="overflow-hidden ring-1 ring-inset ring-slate-200">
            <div className="flex items-baseline justify-between border-b border-slate-100 px-6 py-4">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Top Priority Projects
                </div>
                <div className="mt-0.5 text-sm text-slate-500">
                  Highest and High-priority work in flight
                </div>
              </div>
              <div className="text-xs text-slate-500">
                {topProjects.length} of {activeCount} active
              </div>
            </div>
            <div className="divide-y divide-slate-100">
              {topProjects.map((p, i) => (
                <PriorityProjectRow key={p.id} project={p} index={i} />
              ))}
              {topProjects.length === 0 && (
                <div className="px-6 py-10 text-center text-sm text-slate-500">
                  No high-priority active projects.
                </div>
              )}
            </div>
          </Card>
        </motion.div>
      </div>
    </>
  );
}
