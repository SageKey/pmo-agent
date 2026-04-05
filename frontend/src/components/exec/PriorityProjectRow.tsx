import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import type { Project } from "@/types/project";
import { PriorityPill } from "@/components/portfolio/PriorityPill";
import { HealthBadge } from "@/components/portfolio/HealthBadge";
import { avatarTone, initials, pct, relativeDate } from "@/lib/format";
import { cn } from "@/lib/cn";

const RELATIVE_TONE: Record<string, string> = {
  past: "text-red-600",
  soon: "text-amber-600",
  future: "text-slate-500",
  none: "text-slate-400",
};

export function PriorityProjectRow({
  project,
  index = 0,
}: {
  project: Project;
  index?: number;
}) {
  const rel = relativeDate(project.end_date);
  const completion = Math.min(Math.max(project.pct_complete, 0), 1);
  const avatarClass = avatarTone(project.pm);

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, delay: 0.05 * index }}
    >
      <Link
        to={`/portfolio/${project.id}`}
        className="group flex items-center gap-4 px-6 py-3.5 transition-colors hover:bg-slate-50"
      >
        <div
          className={cn(
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
            avatarClass,
          )}
          title={project.pm ?? ""}
        >
          {initials(project.pm)}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <div className="truncate text-sm font-medium text-slate-900 group-hover:text-navy-700">
              {project.name}
            </div>
            <PriorityPill priority={project.priority} />
          </div>
          <div className="mt-0.5 flex items-center gap-3 text-xs text-slate-500">
            <span className="font-mono">{project.id}</span>
            {project.portfolio && <span className="truncate">{project.portfolio}</span>}
            <span className={cn("ml-auto md:ml-0", RELATIVE_TONE[rel.tone])}>
              {rel.label}
            </span>
          </div>
        </div>

        <div className="hidden w-48 md:block">
          <div className="flex items-center justify-between text-[11px] font-medium text-slate-500">
            <span>{pct(completion)} complete</span>
            <HealthBadge health={project.health} />
          </div>
          <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-100">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${completion * 100}%` }}
              transition={{ duration: 0.7, delay: 0.2 + index * 0.05 }}
              className={cn(
                "h-full rounded-full",
                completion >= 1
                  ? "bg-emerald-500"
                  : completion >= 0.5
                    ? "bg-navy-500"
                    : "bg-slate-400",
              )}
            />
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
