import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowDown, ArrowUp, ArrowUpDown, FolderSearch } from "lucide-react";
import type { Project } from "@/types/project";
import { Table, TBody, TD, THead, TR } from "@/components/ui/table";
import { HealthBadge } from "./HealthBadge";
import { PriorityPill } from "./PriorityPill";
import { avatarTone, hours, initials, pct, shortDate } from "@/lib/format";
import { cn } from "@/lib/cn";

export type SortKey =
  | "id"
  | "name"
  | "priority"
  | "health"
  | "pct_complete"
  | "est_hours"
  | "start_date"
  | "end_date"
  | "pm";

export interface SortState {
  key: SortKey;
  dir: "asc" | "desc";
}

interface Props {
  projects: Project[];
  sort: SortState;
  onSortChange: (next: SortState) => void;
}

export function ProjectTable({ projects, sort, onSortChange }: Props) {
  if (!projects.length) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-white px-6 py-20 text-center">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-slate-400">
          <FolderSearch className="h-7 w-7" />
        </div>
        <div className="text-sm font-semibold text-slate-700">No projects match</div>
        <div className="mt-1 max-w-sm text-xs text-slate-500">
          Try clearing a filter or adjusting your search. Archived work may still
          match further down the page.
        </div>
      </div>
    );
  }

  const toggleSort = (key: SortKey) => {
    if (sort.key === key) {
      onSortChange({ key, dir: sort.dir === "asc" ? "desc" : "asc" });
    } else {
      onSortChange({ key, dir: "asc" });
    }
  };

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-card">
      <Table>
        <THead>
          <TR>
            <SortTh
              label="PM"
              sortKey="pm"
              currentSort={sort}
              onClick={toggleSort}
              width="w-16"
            />
            <SortTh
              label="ID"
              sortKey="id"
              currentSort={sort}
              onClick={toggleSort}
              width="w-24"
            />
            <SortTh
              label="Project"
              sortKey="name"
              currentSort={sort}
              onClick={toggleSort}
            />
            <SortTh
              label="Priority"
              sortKey="priority"
              currentSort={sort}
              onClick={toggleSort}
            />
            <SortTh
              label="Health"
              sortKey="health"
              currentSort={sort}
              onClick={toggleSort}
            />
            <SortTh
              label="Complete"
              sortKey="pct_complete"
              currentSort={sort}
              onClick={toggleSort}
              align="right"
            />
            <SortTh
              label="Est. hrs"
              sortKey="est_hours"
              currentSort={sort}
              onClick={toggleSort}
              align="right"
            />
            <SortTh
              label="Start"
              sortKey="start_date"
              currentSort={sort}
              onClick={toggleSort}
            />
            <SortTh
              label="End"
              sortKey="end_date"
              currentSort={sort}
              onClick={toggleSort}
            />
          </TR>
        </THead>
        <TBody>
          {projects.map((p, i) => (
            <motion.tr
              key={p.id}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.22, delay: Math.min(i * 0.008, 0.12) }}
              className="border-b border-slate-100 transition-colors hover:bg-slate-50/70"
            >
              <TD>
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full text-[11px] font-semibold",
                    avatarTone(p.pm),
                  )}
                  title={p.pm ?? ""}
                >
                  {initials(p.pm)}
                </div>
              </TD>
              <TD className="whitespace-nowrap">
                <span className="inline-flex items-center rounded-md bg-slate-100 px-1.5 py-0.5 font-mono text-[11px] font-medium text-slate-600">
                  {p.id}
                </span>
              </TD>
              <TD className="min-w-[240px]">
                <Link
                  to={`/portfolio/${p.id}`}
                  className="font-medium text-slate-900 hover:text-navy-700"
                >
                  {p.name}
                </Link>
                {p.portfolio && (
                  <div className="text-xs text-slate-500">{p.portfolio}</div>
                )}
              </TD>
              <TD className="whitespace-nowrap">
                <PriorityPill priority={p.priority} />
              </TD>
              <TD className="whitespace-nowrap">
                <HealthBadge health={p.health} />
              </TD>
              <TD className="whitespace-nowrap text-right tabular-nums text-slate-700">
                {pct(p.pct_complete)}
              </TD>
              <TD className="whitespace-nowrap text-right tabular-nums text-slate-700">
                {hours(p.est_hours)}
              </TD>
              <TD className="whitespace-nowrap text-slate-600">
                {shortDate(p.start_date)}
              </TD>
              <TD className="whitespace-nowrap text-slate-600">
                {shortDate(p.end_date)}
              </TD>
            </motion.tr>
          ))}
        </TBody>
      </Table>
    </div>
  );
}

function SortTh({
  label,
  sortKey,
  currentSort,
  onClick,
  align = "left",
  width,
}: {
  label: string;
  sortKey?: SortKey;
  currentSort?: SortState;
  onClick?: (key: SortKey) => void;
  align?: "left" | "right";
  width?: string;
}) {
  const isActive = sortKey && currentSort?.key === sortKey;
  const Arrow =
    isActive && currentSort?.dir === "asc"
      ? ArrowUp
      : isActive && currentSort?.dir === "desc"
        ? ArrowDown
        : ArrowUpDown;

  const content = (
    <span
      className={cn(
        "inline-flex items-center gap-1.5",
        align === "right" && "justify-end",
      )}
    >
      {label}
      {sortKey && (
        <Arrow
          className={cn(
            "h-3 w-3 transition-opacity",
            isActive ? "text-slate-900" : "text-slate-300",
          )}
        />
      )}
    </span>
  );

  return (
    <th
      className={cn(
        "h-10 whitespace-nowrap px-3 align-middle text-xs font-semibold uppercase tracking-wide text-slate-600",
        align === "right" && "text-right",
        width,
        sortKey && "cursor-pointer select-none hover:text-slate-900",
      )}
      onClick={sortKey && onClick ? () => onClick(sortKey) : undefined}
    >
      {content}
    </th>
  );
}
