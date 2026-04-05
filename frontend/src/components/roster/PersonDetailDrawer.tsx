import { AnimatePresence, motion } from "framer-motion";
import { Pencil, Trash2, X } from "lucide-react";
import { Link } from "react-router-dom";
import type { PersonDemand, TeamMember } from "@/types/roster";
import { avatarTone, initials, pct } from "@/lib/format";
import { useDeleteMember } from "@/hooks/useRoster";
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

const STATUS_STYLE: Record<string, string> = {
  GREEN: "text-emerald-700",
  YELLOW: "text-amber-700",
  RED: "text-red-700",
};

export function PersonDetailDrawer({
  person,
  roster,
  onClose,
  onEdit,
}: {
  person: PersonDemand | null;
  roster: TeamMember[];
  onClose: () => void;
  onEdit: (m: TeamMember) => void;
}) {
  const deleteMutation = useDeleteMember();
  const memberRecord = person
    ? roster.find((m) => m.name === person.name) ?? null
    : null;

  const handleDelete = () => {
    if (!person) return;
    if (
      confirm(
        `Delete ${person.name}? This removes them from the roster and unassigns them from every project.`,
      )
    ) {
      deleteMutation.mutate(person.name, {
        onSuccess: () => onClose(),
      });
    }
  };

  return (
    <AnimatePresence>
      {person && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-slate-900/30"
            onClick={onClose}
          />
          <motion.aside
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="fixed inset-y-0 right-0 z-50 w-full max-w-md overflow-y-auto border-l border-slate-200 bg-white shadow-2xl"
          >
            <div className="flex items-start justify-between border-b border-slate-100 px-6 py-5">
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    "flex h-12 w-12 items-center justify-center rounded-full text-sm font-semibold",
                    avatarTone(person.name),
                  )}
                >
                  {initials(person.name)}
                </div>
                <div>
                  <div className="text-base font-semibold text-slate-900">
                    {person.name}
                  </div>
                  <div className="text-xs text-slate-500">
                    {ROLE_LABEL[person.role_key] ?? person.role}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => memberRecord && onEdit(memberRecord)}
                  disabled={!memberRecord}
                  className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 disabled:opacity-40"
                  title="Edit member"
                >
                  <Pencil className="h-4 w-4" />
                </button>
                <button
                  onClick={handleDelete}
                  disabled={deleteMutation.isPending}
                  className="rounded-md p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
                  title="Delete member"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
                <button
                  onClick={onClose}
                  className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="space-y-5 px-6 py-5">
              <div className="grid grid-cols-3 gap-3">
                <Stat
                  label="Utilization"
                  value={pct(person.utilization_pct)}
                  className={STATUS_STYLE[person.status]}
                />
                <Stat
                  label="Load"
                  value={`${person.total_weekly_hrs.toFixed(0)}h`}
                  sub={`of ${person.capacity_hrs.toFixed(0)}h capacity`}
                />
                <Stat
                  label="Projects"
                  value={`${person.project_count}`}
                />
              </div>

              <div>
                <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Assignments
                </div>
                {person.projects.length === 0 && (
                  <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-xs text-slate-500">
                    No current assignments
                  </div>
                )}
                {person.projects.length > 0 && (
                  <ul className="divide-y divide-slate-100 overflow-hidden rounded-lg border border-slate-200">
                    {person.projects
                      .slice()
                      .sort((a, b) => b.weekly_hours - a.weekly_hours)
                      .map((p) => (
                        <li key={`${p.project_id}-${p.role_key}`}>
                          <Link
                            to={`/portfolio/${p.project_id}`}
                            className="flex items-center gap-3 px-4 py-2.5 transition-colors hover:bg-slate-50"
                          >
                            <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] font-medium text-slate-600">
                              {p.project_id}
                            </span>
                            <span className="min-w-0 flex-1 truncate text-sm text-slate-800">
                              {p.project_name}
                            </span>
                            <span className="shrink-0 text-xs tabular-nums text-slate-500">
                              {p.weekly_hours.toFixed(1)}h/wk
                            </span>
                          </Link>
                        </li>
                      ))}
                  </ul>
                )}
              </div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

function Stat({
  label,
  value,
  sub,
  className,
}: {
  label: string;
  value: string;
  sub?: string;
  className?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
        {label}
      </div>
      <div
        className={cn(
          "mt-0.5 text-lg font-bold tabular-nums text-slate-900",
          className,
        )}
      >
        {value}
      </div>
      {sub && <div className="text-[10px] text-slate-500">{sub}</div>}
    </div>
  );
}
