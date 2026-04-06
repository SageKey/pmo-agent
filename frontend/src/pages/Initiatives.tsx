import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Target,
  Monitor,
  Building2,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { Link } from "react-router-dom";
import { TopBar } from "@/components/layout/TopBar";
import { Card } from "@/components/ui/card";
import { useInitiatives } from "@/hooks/useInitiatives";
import { cn } from "@/lib/cn";
import type { Initiative, InitiativeProjectSummary } from "@/types/initiative";

const PRIORITY_BG: Record<string, string> = {
  Highest: "bg-red-100 text-red-700",
  High: "bg-amber-100 text-amber-700",
  Medium: "bg-slate-100 text-slate-700",
  Low: "bg-slate-50 text-slate-500",
};


export function Initiatives() {
  const { data, isLoading } = useInitiatives();
  const initiatives = data ?? [];

  // Group by status
  const grouped = useMemo(() => {
    const groups = new Map<string, Initiative[]>();
    for (const status of ["Active", "On Hold", "Complete"]) {
      groups.set(status, []);
    }
    for (const init of initiatives) {
      const list = groups.get(init.status) ?? [];
      list.push(init);
      groups.set(init.status, list);
    }
    return Array.from(groups.entries()).filter(([, list]) => list.length > 0);
  }, [initiatives]);

  // Counts
  const itCount = initiatives.filter((i) => i.it_involvement).length;
  const nonItCount = initiatives.length - itCount;
  const totalProjects = initiatives.reduce((s, i) => s + i.project_count, 0);

  return (
    <>
      <TopBar
        title="Key Initiatives"
        subtitle={`${initiatives.length} strategic initiatives driving the business forward.`}
      />
      <div className="space-y-6 p-8">
        {/* Summary strip */}
        <div className="grid gap-4 md:grid-cols-3">
          <SummaryCard
            icon={<Target className="h-5 w-5" />}
            label="Total initiatives"
            value={initiatives.length}
            tone="navy"
          />
          <SummaryCard
            icon={<Monitor className="h-5 w-5" />}
            label="IT involvement"
            value={itCount}
            sub={`${nonItCount} non-IT`}
            tone="sky"
          />
          <SummaryCard
            icon={<Building2 className="h-5 w-5" />}
            label="Linked IT projects"
            value={totalProjects}
            tone="emerald"
          />
        </div>

        {isLoading && (
          <Card className="py-16 text-center text-sm text-slate-500">
            Loading initiatives…
          </Card>
        )}

        {/* Grouped list */}
        {grouped.map(([status, list]) => (
          <section key={status} className="space-y-3">
            <div className="flex items-baseline gap-2">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-900">
                {status}
              </h2>
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold tabular-nums text-slate-600">
                {list.length}
              </span>
            </div>
            <Card className="overflow-hidden divide-y divide-slate-100">
              {/* Header */}
              <div className="grid grid-cols-12 gap-4 bg-slate-50 px-5 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                <div className="col-span-4">Initiative</div>
                <div className="col-span-2">Sponsor</div>
                <div className="col-span-1 text-center">IT</div>
                <div className="col-span-1 text-center">Priority</div>
                <div className="col-span-2">Timeline</div>
                <div className="col-span-2 text-right">IT Projects</div>
              </div>
              {list.map((init, i) => (
                <InitiativeRow key={init.id} initiative={init} delay={i * 0.03} />
              ))}
            </Card>
          </section>
        ))}
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------

function SummaryCard({
  icon,
  label,
  value,
  sub,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  sub?: string;
  tone: "navy" | "sky" | "emerald";
}) {
  const toneMap = {
    navy: "from-navy-50 to-white text-navy-700 ring-navy-200",
    sky: "from-sky-50 to-white text-sky-700 ring-sky-200",
    emerald: "from-emerald-50 to-white text-emerald-700 ring-emerald-200",
  };
  return (
    <Card
      className={cn(
        "flex items-center gap-4 bg-gradient-to-r px-5 py-4 ring-1 ring-inset",
        toneMap[tone],
      )}
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white/70 ring-1 ring-inset ring-white">
        {icon}
      </div>
      <div>
        <div className="text-2xl font-bold tabular-nums">{value}</div>
        <div className="text-xs opacity-80">
          {label}
          {sub && <span className="ml-1 opacity-60">({sub})</span>}
        </div>
      </div>
    </Card>
  );
}

function InitiativeRow({
  initiative: init,
  delay,
}: {
  initiative: Initiative;
  delay: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const hasProjects = init.project_count > 0;

  return (
    <motion.div
      initial={{ opacity: 0, x: -4 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2, delay }}
    >
      <button
        type="button"
        onClick={() => hasProjects && setExpanded(!expanded)}
        className={cn(
          "grid w-full grid-cols-12 items-center gap-4 px-5 py-3 text-left transition-colors",
          hasProjects && "hover:bg-slate-50 cursor-pointer",
          !hasProjects && "cursor-default",
        )}
      >
        <div className="col-span-4 flex items-center gap-2">
          {hasProjects ? (
            expanded ? (
              <ChevronDown className="h-3.5 w-3.5 shrink-0 text-slate-400" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5 shrink-0 text-slate-400" />
            )
          ) : (
            <span className="w-3.5" />
          )}
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold text-slate-800">
              {init.name}
            </div>
            <div className="mt-0.5 text-[11px] text-slate-500 font-mono">
              {init.id}
            </div>
          </div>
        </div>

        <div className="col-span-2 text-xs text-slate-600 truncate">
          {init.sponsor ?? "—"}
        </div>

        <div className="col-span-1 text-center">
          {init.it_involvement ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-sky-100 px-2 py-0.5 text-[10px] font-semibold text-sky-700">
              <Monitor className="h-3 w-3" />
              IT
            </span>
          ) : (
            <span className="text-[10px] font-medium text-slate-400">—</span>
          )}
        </div>

        <div className="col-span-1 text-center">
          <span
            className={cn(
              "rounded-full px-2 py-0.5 text-[10px] font-semibold",
              PRIORITY_BG[init.priority ?? ""] ?? PRIORITY_BG.Medium,
            )}
          >
            {init.priority ?? "—"}
          </span>
        </div>

        <div className="col-span-2 text-xs text-slate-500 tabular-nums">
          {init.target_start && init.target_end ? (
            <>
              {init.target_start.slice(0, 7)} → {init.target_end.slice(0, 7)}
            </>
          ) : (
            "—"
          )}
        </div>

        <div className="col-span-2 text-right">
          {hasProjects ? (
            <ProjectHealthSummary projects={init.projects} />
          ) : (
            <span className="text-xs text-slate-400">No IT projects</span>
          )}
        </div>
      </button>

      {/* Expanded child projects */}
      {expanded && hasProjects && (
        <div className="border-t border-slate-100 bg-slate-50/50 px-5 py-3 pl-12">
          <div className="space-y-2">
            {init.projects.map((p) => (
              <ChildProjectRow key={p.id} project={p} />
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}

function ProjectHealthSummary({
  projects,
}: {
  projects: InitiativeProjectSummary[];
}) {
  const pipeline = projects.filter(
    (p) => p.health && p.health.toUpperCase().includes("PIPELINE"),
  ).length;
  const complete = projects.filter(
    (p) => p.health && p.health.toUpperCase().includes("COMPLETE"),
  ).length;
  const active = projects.length - pipeline - complete;

  return (
    <div className="flex items-center justify-end gap-2 text-[11px]">
      {active > 0 && (
        <span className="rounded-full bg-emerald-50 px-2 py-0.5 font-semibold text-emerald-700">
          {active} active
        </span>
      )}
      {pipeline > 0 && (
        <span className="rounded-full bg-slate-100 px-2 py-0.5 font-semibold text-slate-600">
          {pipeline} pipeline
        </span>
      )}
      {complete > 0 && (
        <span className="rounded-full bg-slate-50 px-2 py-0.5 font-semibold text-slate-400">
          {complete} done
        </span>
      )}
    </div>
  );
}

function ChildProjectRow({
  project: p,
}: {
  project: InitiativeProjectSummary;
}) {
  const isPipeline =
    p.health && p.health.toUpperCase().includes("PIPELINE");

  return (
    <div className="flex items-center gap-3">
      <Link
        to={`/portfolio/${p.id}`}
        className="truncate text-sm font-medium text-navy-700 hover:text-navy-900"
      >
        {p.name}
      </Link>
      <span className="text-[10px] font-mono text-slate-400">{p.id}</span>
      {p.priority && (
        <span
          className={cn(
            "rounded-full px-2 py-0.5 text-[10px] font-semibold",
            PRIORITY_BG[p.priority] ?? PRIORITY_BG.Medium,
          )}
        >
          {p.priority}
        </span>
      )}
      {isPipeline ? (
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
          Pipeline {p.planned_it_start ?? ""}
        </span>
      ) : (
        <span className="text-xs tabular-nums text-slate-500">
          {Math.round(p.pct_complete * 100)}%
        </span>
      )}
    </div>
  );
}
