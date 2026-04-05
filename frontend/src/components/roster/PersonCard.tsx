import { motion } from "framer-motion";
import type { PersonDemand } from "@/types/roster";
import { Card } from "@/components/ui/card";
import { avatarTone, initials, pct } from "@/lib/format";
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

const STATUS_STYLE: Record<
  string,
  { bar: string; text: string; ring: string; chip: string }
> = {
  GREEN: {
    bar: "bg-emerald-500",
    text: "text-emerald-700",
    ring: "ring-emerald-200",
    chip: "bg-emerald-50 text-emerald-700",
  },
  YELLOW: {
    bar: "bg-amber-500",
    text: "text-amber-700",
    ring: "ring-amber-200",
    chip: "bg-amber-50 text-amber-700",
  },
  RED: {
    bar: "bg-red-500",
    text: "text-red-700",
    ring: "ring-red-200",
    chip: "bg-red-50 text-red-700",
  },
};

export function PersonCard({
  person,
  index = 0,
  onClick,
}: {
  person: PersonDemand;
  index?: number;
  onClick?: () => void;
}) {
  const s = STATUS_STYLE[person.status] ?? STATUS_STYLE.GREEN;
  const width = Math.min(person.utilization_pct, 1.5) * 100;

  return (
    <motion.button
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: Math.min(index * 0.02, 0.2) }}
      onClick={onClick}
      className="group block w-full text-left"
    >
      <Card
        className={cn(
          "ring-1 ring-inset transition-all hover:-translate-y-0.5 hover:shadow-elev",
          s.ring,
        )}
      >
        <div className="p-5">
          <div className="flex items-start gap-3">
            <div
              className={cn(
                "flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
                avatarTone(person.name),
              )}
            >
              {initials(person.name)}
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-semibold text-slate-900">
                {person.name}
              </div>
              <div className="mt-0.5 text-xs text-slate-500">
                {ROLE_LABEL[person.role_key] ?? person.role}
              </div>
            </div>
            <span
              className={cn(
                "shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold",
                s.chip,
              )}
            >
              {pct(person.utilization_pct)}
            </span>
          </div>

          <div className="mt-4">
            <div className="mb-1 flex items-center justify-between text-[11px] text-slate-500">
              <span className="tabular-nums">
                {person.total_weekly_hrs.toFixed(0)} / {person.capacity_hrs.toFixed(0)} hrs/wk
              </span>
              <span>
                {person.project_count} project{person.project_count === 1 ? "" : "s"}
              </span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${width}%` }}
                transition={{ duration: 0.6, delay: 0.2 + index * 0.02 }}
                className={cn("h-full rounded-full", s.bar)}
              />
            </div>
          </div>
        </div>
      </Card>
    </motion.button>
  );
}
