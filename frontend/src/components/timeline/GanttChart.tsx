import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import type { Project } from "@/types/project";
import { Card } from "@/components/ui/card";
import { avatarTone, initials, pct, shortDate } from "@/lib/format";
import { cn } from "@/lib/cn";

const PRIORITY_BAR: Record<string, { bar: string; fill: string; text: string }> = {
  Highest: { bar: "bg-red-200", fill: "bg-red-500", text: "text-red-900" },
  High: { bar: "bg-amber-200", fill: "bg-amber-500", text: "text-amber-900" },
  Medium: { bar: "bg-sky-200", fill: "bg-sky-500", text: "text-sky-900" },
  Low: { bar: "bg-slate-200", fill: "bg-slate-500", text: "text-slate-800" },
};

function addMonths(d: Date, n: number): Date {
  const r = new Date(d);
  r.setMonth(r.getMonth() + n);
  return r;
}

function monthStart(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

function monthsBetween(a: Date, b: Date): number {
  return (b.getFullYear() - a.getFullYear()) * 12 + (b.getMonth() - a.getMonth());
}

function toDate(iso?: string | null): Date | null {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d;
}

export interface GanttProps {
  projects: Project[];
  /** First visible month (Date at day 1). */
  rangeStart: Date;
  /** Last visible month (Date at day 1). */
  rangeEnd: Date;
  /** Pixel width per month column. */
  monthWidth?: number;
}

export function GanttChart({
  projects,
  rangeStart,
  rangeEnd,
  monthWidth = 80,
}: GanttProps) {
  const totalMonths = monthsBetween(rangeStart, rangeEnd) + 1;
  const totalWidth = totalMonths * monthWidth;

  // Build the month column headers
  const months: { date: Date; label: string; isJan: boolean }[] = [];
  for (let i = 0; i < totalMonths; i++) {
    const d = addMonths(rangeStart, i);
    months.push({
      date: d,
      label: `${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`,
      isJan: d.getMonth() === 0,
    });
  }

  // Today line position
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayOffsetMonths =
    monthsBetween(rangeStart, today) +
    today.getDate() / daysInMonth(today.getFullYear(), today.getMonth());
  const todayInRange = todayOffsetMonths >= 0 && todayOffsetMonths <= totalMonths;
  const todayX = todayOffsetMonths * monthWidth;

  // Filter projects with valid dates AND that overlap the range
  const rangeStartMs = rangeStart.getTime();
  const rangeEndMs = addMonths(rangeEnd, 1).getTime(); // end-exclusive next month
  const scheduled = projects
    .map((p) => {
      const s = toDate(p.start_date);
      const e = toDate(p.end_date);
      if (!s || !e) return null;
      if (e.getTime() < rangeStartMs || s.getTime() > rangeEndMs) return null;
      return { project: p, start: s, end: e };
    })
    .filter((x): x is { project: Project; start: Date; end: Date } => x !== null);

  const LEFT_COL = 260;

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Project Gantt
          </div>
          <div className="mt-0.5 text-xs text-slate-500">
            {scheduled.length} scheduled projects ·{" "}
            {`${String(rangeStart.getMonth() + 1).padStart(2, "0")}-${rangeStart.getFullYear()}`}{" "}
            →{" "}
            {`${String(rangeEnd.getMonth() + 1).padStart(2, "0")}-${rangeEnd.getFullYear()}`}
          </div>
        </div>
        <Legend />
      </div>

      <div className="overflow-x-auto">
        <div style={{ minWidth: LEFT_COL + totalWidth }}>
          {/* Month header row */}
          <div className="sticky top-0 z-10 flex border-b border-slate-200 bg-slate-50">
            <div
              style={{ width: LEFT_COL }}
              className="shrink-0 border-r border-slate-200 px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500"
            >
              Project
            </div>
            <div className="relative" style={{ width: totalWidth }}>
              <div className="flex h-full">
                {months.map((m, i) => (
                  <div
                    key={i}
                    style={{ width: monthWidth }}
                    className={cn(
                      "flex items-center justify-center border-r border-slate-200 py-2 text-[11px]",
                      m.isJan ? "bg-slate-100 font-semibold" : "bg-slate-50",
                    )}
                  >
                    <span className={m.isJan ? "text-slate-700" : "text-slate-500"}>
                      {m.label}
                      {m.isJan && (
                        <span className="ml-1 text-[9px] text-slate-400">
                          {m.date.getFullYear()}
                        </span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Rows + overlays */}
          <div className="relative">
            {/* Today line */}
            {todayInRange && (
              <div
                className="pointer-events-none absolute top-0 z-20"
                style={{
                  left: LEFT_COL + todayX,
                  height: `${scheduled.length * 44}px`,
                }}
              >
                <div className="h-full w-px bg-red-400" />
                <div className="absolute -top-5 -translate-x-1/2 rounded bg-red-500 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-white">
                  Today
                </div>
              </div>
            )}

            {/* Project rows */}
            {scheduled.map(({ project, start, end }, i) => (
              <GanttRow
                key={project.id}
                project={project}
                start={start}
                end={end}
                rangeStart={rangeStart}
                totalMonths={totalMonths}
                monthWidth={monthWidth}
                leftCol={LEFT_COL}
                rowIndex={i}
              />
            ))}

            {scheduled.length === 0 && (
              <div className="py-16 text-center text-sm text-slate-500">
                No scheduled projects in this date range.
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}

function GanttRow({
  project,
  start,
  end,
  rangeStart,
  totalMonths,
  monthWidth,
  leftCol,
  rowIndex,
}: {
  project: Project;
  start: Date;
  end: Date;
  rangeStart: Date;
  totalMonths: number;
  monthWidth: number;
  leftCol: number;
  rowIndex: number;
}) {
  const colors =
    PRIORITY_BAR[project.priority ?? "Low"] ?? PRIORITY_BAR.Low;

  const startOffset = monthsFractional(rangeStart, start);
  const endOffset = monthsFractional(rangeStart, end);
  const clampedStart = Math.max(0, startOffset);
  const clampedEnd = Math.min(totalMonths, endOffset);
  const x = clampedStart * monthWidth;
  const width = Math.max((clampedEnd - clampedStart) * monthWidth, 6);

  const completion = Math.min(Math.max(project.pct_complete, 0), 1);

  return (
    <motion.div
      initial={{ opacity: 0, x: -4 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.25, delay: Math.min(rowIndex * 0.01, 0.15) }}
      className="flex border-b border-slate-100 hover:bg-slate-50/80"
    >
      {/* Left: project label */}
      <div
        style={{ width: leftCol }}
        className="flex shrink-0 items-center gap-2 border-r border-slate-200 px-3 py-2"
      >
        <div
          className={cn(
            "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold",
            avatarTone(project.pm),
          )}
          title={project.pm ?? ""}
        >
          {initials(project.pm)}
        </div>
        <div className="min-w-0 flex-1">
          <Link
            to={`/portfolio/${project.id}`}
            className="block truncate text-xs font-medium text-slate-900 hover:text-navy-700"
          >
            {project.name}
          </Link>
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
            <span className="font-mono">{project.id}</span>
            <span>·</span>
            <span>{project.priority ?? "—"}</span>
          </div>
        </div>
      </div>

      {/* Right: bar track */}
      <div className="relative" style={{ width: totalMonths * monthWidth, height: 44 }}>
        {/* Month gridlines */}
        <div className="absolute inset-0 flex pointer-events-none">
          {Array.from({ length: totalMonths }).map((_, i) => (
            <div
              key={i}
              style={{ width: monthWidth }}
              className="h-full border-r border-slate-100"
            />
          ))}
        </div>

        {/* The bar */}
        <div
          className={cn(
            "group absolute top-1/2 -translate-y-1/2 rounded-md ring-1 ring-inset",
            colors.bar,
            "ring-black/5",
          )}
          style={{ left: x, width, height: 22 }}
          title={`${project.name} · ${shortDate(project.start_date)} → ${shortDate(project.end_date)} · ${pct(completion)}`}
        >
          {/* Progress fill */}
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${completion * 100}%` }}
            transition={{
              duration: 0.7,
              delay: 0.2 + rowIndex * 0.01,
              ease: "easeOut",
            }}
            className={cn("h-full rounded-md", colors.fill)}
          />
          {/* Label inside the bar */}
          <div
            className={cn(
              "pointer-events-none absolute inset-0 flex items-center px-2 text-[10px] font-semibold",
              completion > 0.5 ? "text-white" : colors.text,
            )}
          >
            <span className="truncate">
              {width > 40 ? `${Math.round(completion * 100)}%` : ""}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function Legend() {
  return (
    <div className="flex items-center gap-3 text-[10px] text-slate-500">
      {(["Highest", "High", "Medium", "Low"] as const).map((p) => (
        <div key={p} className="flex items-center gap-1.5">
          <div className={cn("h-2 w-4 rounded", PRIORITY_BAR[p].fill)} />
          <span>{p}</span>
        </div>
      ))}
    </div>
  );
}

function daysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
}

/** Fractional offset in months between `anchor` and `d`, including the day within month. */
function monthsFractional(anchor: Date, d: Date): number {
  const whole = monthsBetween(monthStart(anchor), monthStart(d));
  const dayFrac =
    (d.getDate() - 1) / daysInMonth(d.getFullYear(), d.getMonth());
  return whole + dayFrac;
}
