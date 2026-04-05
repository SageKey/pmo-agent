import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight } from "lucide-react";
import type { Project } from "@/types/project";
import { ProjectTable, type SortState } from "./ProjectTable";
import { cn } from "@/lib/cn";

interface Props {
  title: string;
  subtitle?: string;
  count: number;
  projects: Project[];
  sort: SortState;
  onSortChange: (next: SortState) => void;
  expanded: boolean;
  onToggle: () => void;
  /** Shown as a small badge next to the count when filters are active and
   *  auto-expanded the group (e.g. "2 matches"). */
  matchBadge?: string;
  /** When true, style the group as secondary / quieter (Archive). */
  muted?: boolean;
}

export function ProjectGroup({
  title,
  subtitle,
  count,
  projects,
  sort,
  onSortChange,
  expanded,
  onToggle,
  matchBadge,
  muted = false,
}: Props) {
  return (
    <section>
      <button
        type="button"
        onClick={onToggle}
        className={cn(
          "group flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left transition-colors hover:bg-slate-100",
        )}
      >
        <motion.div
          animate={{ rotate: expanded ? 90 : 0 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className="flex h-5 w-5 items-center justify-center text-slate-400 group-hover:text-slate-700"
        >
          <ChevronRight className="h-4 w-4" />
        </motion.div>
        <div className="flex items-baseline gap-2">
          <h2
            className={cn(
              "text-sm font-semibold uppercase tracking-wide",
              muted ? "text-slate-500" : "text-slate-900",
            )}
          >
            {title}
          </h2>
          <span
            className={cn(
              "rounded-full px-2 py-0.5 text-[11px] font-semibold tabular-nums",
              muted
                ? "bg-slate-100 text-slate-500"
                : "bg-navy-900 text-white",
            )}
          >
            {count}
          </span>
          {subtitle && (
            <span className="text-xs text-slate-500">· {subtitle}</span>
          )}
          {matchBadge && (
            <span className="ml-1 rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-medium text-amber-800 ring-1 ring-inset ring-amber-200">
              {matchBadge}
            </span>
          )}
        </div>
      </button>

      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="content"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className={cn("mt-3", muted && "opacity-90")}>
              <ProjectTable
                projects={projects}
                sort={sort}
                onSortChange={onSortChange}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
