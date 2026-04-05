import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { GanttChart } from "@/components/timeline/GanttChart";
import { usePortfolio } from "@/hooks/usePortfolio";
import { cn } from "@/lib/cn";

const PRIORITY_ORDER: Record<string, number> = {
  Highest: 0,
  High: 1,
  Medium: 2,
  Low: 3,
};

type SortKey = "start" | "priority" | "name";

export function Timeline() {
  const [search, setSearch] = useState("");
  const [activeOnly, setActiveOnly] = useState(true);
  const [priorityFilter, setPriorityFilter] = useState<Set<string>>(new Set());
  const [sort, setSort] = useState<SortKey>("start");

  const { data, isLoading, isError, error } = usePortfolio(false);

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = search.trim().toLowerCase();
    return data.filter((p) => {
      if (!p.start_date || !p.end_date) return false;
      if (activeOnly && !p.is_active) return false;
      if (q) {
        const hay = `${p.id} ${p.name} ${p.pm ?? ""}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      if (priorityFilter.size > 0 && !priorityFilter.has(p.priority ?? "")) {
        return false;
      }
      return true;
    });
  }, [data, search, activeOnly, priorityFilter]);

  const sorted = useMemo(() => {
    const out = [...filtered];
    out.sort((a, b) => {
      if (sort === "start") {
        const as = a.start_date ? new Date(a.start_date).getTime() : 0;
        const bs = b.start_date ? new Date(b.start_date).getTime() : 0;
        return as - bs;
      }
      if (sort === "priority") {
        return (
          (PRIORITY_ORDER[a.priority ?? "Low"] ?? 99) -
          (PRIORITY_ORDER[b.priority ?? "Low"] ?? 99)
        );
      }
      return a.name.localeCompare(b.name);
    });
    return out;
  }, [filtered, sort]);

  const { rangeStart, rangeEnd } = useMemo(() => {
    const today = new Date();
    const defaultStart = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    const defaultEnd = new Date(2027, 11, 1); // through end of 2027

    if (sorted.length === 0) {
      return { rangeStart: defaultStart, rangeEnd: defaultEnd };
    }

    let minStart = defaultStart;
    let maxEnd = defaultEnd;
    for (const p of sorted) {
      const s = p.start_date ? new Date(p.start_date) : null;
      const e = p.end_date ? new Date(p.end_date) : null;
      if (s && s < minStart) minStart = new Date(s.getFullYear(), s.getMonth(), 1);
      if (e && e > maxEnd) maxEnd = new Date(e.getFullYear(), e.getMonth(), 1);
    }
    return { rangeStart: minStart, rangeEnd: maxEnd };
  }, [sorted]);

  const togglePriority = (p: string) => {
    const next = new Set(priorityFilter);
    next.has(p) ? next.delete(p) : next.add(p);
    setPriorityFilter(next);
  };

  return (
    <>
      <TopBar
        title="Timeline"
        subtitle="Forward-looking Gantt across the active portfolio."
      />
      <div className="space-y-5 p-8">
        {/* Toolbar */}
        <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-card">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative min-w-[240px] flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search projects…"
                className="w-full rounded-md border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
            </div>

            <div className="inline-flex overflow-hidden rounded-md border border-slate-200">
              <button
                onClick={() => setActiveOnly(true)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium transition-colors",
                  activeOnly
                    ? "bg-navy-900 text-white"
                    : "bg-white text-slate-600 hover:bg-slate-50",
                )}
              >
                In flight
              </button>
              <button
                onClick={() => setActiveOnly(false)}
                className={cn(
                  "border-l border-slate-200 px-3 py-1.5 text-xs font-medium transition-colors",
                  !activeOnly
                    ? "bg-navy-900 text-white"
                    : "bg-white text-slate-600 hover:bg-slate-50",
                )}
              >
                All
              </button>
            </div>

            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as SortKey)}
              className="rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
            >
              <option value="start">Sort by start date</option>
              <option value="priority">Sort by priority</option>
              <option value="name">Sort by name</option>
            </select>

            <div className="ml-auto text-xs text-slate-500 tabular-nums">
              <span className="font-semibold text-slate-900">{sorted.length}</span>{" "}
              scheduled
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="mr-1 font-semibold uppercase tracking-wider text-slate-400">
              Priority
            </span>
            {(["Highest", "High", "Medium", "Low"] as const).map((p) => (
              <Chip
                key={p}
                active={priorityFilter.has(p)}
                onClick={() => togglePriority(p)}
              >
                {p}
              </Chip>
            ))}
          </div>
        </div>

        {isLoading && (
          <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-500">
            Loading…
          </div>
        )}
        {isError && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-800">
            Failed to load: {(error as Error).message}
          </div>
        )}

        {data && (
          <GanttChart
            projects={sorted}
            rangeStart={rangeStart}
            rangeEnd={rangeEnd}
          />
        )}
      </div>
    </>
  );
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset transition-colors",
        active
          ? "bg-navy-900 text-white ring-navy-900"
          : "bg-white text-slate-600 ring-slate-200 hover:bg-slate-50 hover:text-slate-900",
      )}
    >
      {children}
    </button>
  );
}
