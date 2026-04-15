import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Briefcase, CheckCircle2, Circle, Monitor, Plus } from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { Button } from "@/components/ui/button";
import { InitiativeDialog } from "@/components/initiatives/InitiativeDialog";
import { useInitiatives } from "@/hooks/useInitiatives";
import { cn } from "@/lib/cn";
import { shortMonthYear } from "@/lib/format";
import type { Initiative } from "@/types/initiative";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PRIORITY_STYLE: Record<string, string> = {
  Highest: "bg-red-100 text-red-700",
  High: "bg-amber-100 text-amber-700",
  Medium: "bg-slate-100 text-slate-700",
  Low: "bg-slate-50 text-slate-500",
};

const GROUP_ORDER = [
  { key: "Active", label: "Active", icon: Circle, color: "text-emerald-600" },
  { key: "On Hold", label: "On Hold", icon: Circle, color: "text-amber-500" },
  { key: "Complete", label: "Complete", icon: CheckCircle2, color: "text-emerald-500" },
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function Initiatives() {
  const { data, isLoading } = useInitiatives();
  const initiatives = data ?? [];
  const [statusTab, setStatusTab] = useState("Active");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Initiative | null>(null);

  const groups = useMemo(() => {
    const map: Record<string, Initiative[]> = { Active: [], "On Hold": [], Complete: [] };
    for (const i of initiatives) {
      const bucket = map[i.status] ?? map.Active;
      bucket.push(i);
    }
    // Sort each group by sort_order, then name
    for (const key of Object.keys(map)) {
      map[key].sort((a, b) => {
        if (a.sort_order !== b.sort_order) return a.sort_order - b.sort_order;
        return a.name.localeCompare(b.name);
      });
    }
    return map;
  }, [initiatives]);

  const openEdit = (init: Initiative) => {
    setEditTarget(init);
    setDialogOpen(true);
  };

  const openCreate = () => {
    setEditTarget(null);
    setDialogOpen(true);
  };

  return (
    <>
      <TopBar
        title="Key Initiatives"
        subtitle={`${initiatives.length} strategic initiatives for 2026`}
      />
      <div className="space-y-0 p-8">
        {/* Toolbar */}
        <div className="mb-4 flex items-center justify-end">
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" />
            New initiative
          </Button>
        </div>

        <InitiativeDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          initiative={editTarget}
        />

        {isLoading && (
          <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-500">Loading initiatives...</div>
        )}

        {/* Status tabs */}
        <div className="border-b border-slate-200 bg-white rounded-t-xl px-4">
          <nav className="flex gap-1">
            {GROUP_ORDER.map(({ key, label, icon: Icon, color }) => {
              const count = (groups[key] ?? []).length;
              return (
                <button
                  key={key}
                  onClick={() => setStatusTab(key)}
                  className={cn(
                    "flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors",
                    statusTab === key
                      ? "border-indigo-600 text-indigo-700"
                      : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300",
                  )}
                >
                  <Icon className={cn("h-4 w-4", statusTab === key ? "text-indigo-600" : color)} />
                  {label}
                  <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600">{count}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Active tab content */}
        <div className="rounded-b-xl border border-t-0 border-slate-200 bg-white overflow-hidden">
          {(groups[statusTab] ?? []).length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-400">
              <CheckCircle2 className="h-8 w-8 mb-2 text-slate-300" />
              <span className="text-sm font-medium">No initiatives in this category</span>
            </div>
          ) : (
            <div className="space-y-2 p-4">
              {(groups[statusTab] ?? []).map((init, i) => (
                <InitiativeRow key={init.id} init={init} index={i} onEdit={openEdit} />
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Initiative Row
// ---------------------------------------------------------------------------

function InitiativeRow({ init, index, onEdit }: { init: Initiative; index: number; onEdit: (i: Initiative) => void }) {
  const priorityStyle = PRIORITY_STYLE[init.priority ?? ""] ?? PRIORITY_STYLE.Medium;

  // Progress = average pct_complete of linked projects
  const projPcts = init.projects.map((p) => p.pct_complete ?? 0);
  const avgPct = projPcts.length > 0
    ? Math.round((projPcts.reduce((s, v) => s + v, 0) / projPcts.length) * 100)
    : 0;
  const hasProjects = init.projects.length > 0;

  return (
    <motion.button
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      onClick={() => onEdit(init)}
      className="flex w-full items-center gap-4 rounded-lg border border-slate-200 bg-white px-5 py-4 text-left transition-all hover:border-slate-300 hover:shadow-sm"
    >
      {/* ID badge */}
      <span className="shrink-0 rounded-md bg-indigo-100 px-2 py-1 text-[10px] font-bold text-indigo-700 tabular-nums">
        {init.id}
      </span>

      {/* Name + meta */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-semibold text-slate-900">{init.name}</span>
          {init.priority && (
            <span className={cn("shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold", priorityStyle)}>
              {init.priority}
            </span>
          )}
        </div>
        <div className="mt-1.5 flex flex-wrap items-center gap-3 text-[11px] text-slate-500">
          {init.sponsor && <span>{init.sponsor}</span>}
          {init.target_start && init.target_end && (
            <span className="tabular-nums">{shortMonthYear(init.target_start)} → {shortMonthYear(init.target_end)}</span>
          )}
          <span className="flex items-center gap-1">
            <Briefcase className="h-3 w-3" />
            {init.project_count} {init.project_count === 1 ? "project" : "projects"}
          </span>
          {init.it_involvement && (
            <span className="flex items-center gap-1 rounded-full bg-sky-50 px-1.5 py-0.5 text-[9px] font-medium text-sky-600">
              <Monitor className="h-2.5 w-2.5" />
              IT Required
            </span>
          )}
        </div>
      </div>

      {/* Progress */}
      <div className="w-20 shrink-0">
        {hasProjects ? (
          <>
            <div className="mb-0.5 text-right text-[11px] font-bold tabular-nums text-slate-700">{avgPct}%</div>
            <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
              <div
                className={cn("h-full rounded-full", avgPct >= 100 ? "bg-emerald-500" : "bg-indigo-500")}
                style={{ width: `${Math.min(100, Math.max(avgPct, 2))}%` }}
              />
            </div>
          </>
        ) : (
          <div className="text-right text-[10px] text-slate-400">No projects</div>
        )}
      </div>
    </motion.button>
  );
}
