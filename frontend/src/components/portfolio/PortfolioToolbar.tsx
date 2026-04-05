import { Search, X, Check } from "lucide-react";
import { cn } from "@/lib/cn";

export interface PortfolioFilters {
  search: string;
  priorities: Set<string>;
  healths: Set<string>;
  pm: string | null;
}

export const PRIORITY_OPTIONS = ["Highest", "High", "Medium", "Low"] as const;
export const HEALTH_OPTIONS = [
  "ON TRACK",
  "AT RISK",
  "NEEDS HELP",
  "NEEDS SPEC",
  "NOT STARTED",
  "COMPLETE",
] as const;

const HEALTH_LABEL: Record<string, string> = {
  "ON TRACK": "On track",
  "AT RISK": "At risk",
  "NEEDS HELP": "Needs help",
  "NEEDS SPEC": "Needs spec",
  "NOT STARTED": "Not started",
  COMPLETE: "Complete",
};

interface Props {
  filters: PortfolioFilters;
  onChange: (next: PortfolioFilters) => void;
  pmOptions: string[];
  totalMatched: number;
  totalAll: number;
}

export function PortfolioToolbar({
  filters,
  onChange,
  pmOptions,
  totalMatched,
  totalAll,
}: Props) {
  const togglePriority = (p: string) => {
    const next = new Set(filters.priorities);
    next.has(p) ? next.delete(p) : next.add(p);
    onChange({ ...filters, priorities: next });
  };
  const toggleHealth = (h: string) => {
    const next = new Set(filters.healths);
    next.has(h) ? next.delete(h) : next.add(h);
    onChange({ ...filters, healths: next });
  };
  const resetAll = () =>
    onChange({
      search: "",
      priorities: new Set(),
      healths: new Set(),
      pm: null,
    });

  const anyFilterActive =
    filters.search !== "" ||
    filters.priorities.size > 0 ||
    filters.healths.size > 0 ||
    filters.pm !== null;

  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-card">
      {/* Row 1: search + active toggle + reset */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={filters.search}
            onChange={(e) => onChange({ ...filters, search: e.target.value })}
            placeholder="Search projects by name, ID, or PM…"
            className="w-full rounded-md border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-navy-100"
          />
        </div>

        <div className="ml-auto flex items-center gap-3 text-xs text-slate-500">
          <span className="tabular-nums">
            <span className="font-semibold text-slate-900">{totalMatched}</span>
            {totalMatched !== totalAll && (
              <span className="text-slate-400"> of {totalAll}</span>
            )}{" "}
            project{totalMatched === 1 ? "" : "s"}
          </span>
          {anyFilterActive && (
            <button
              onClick={resetAll}
              className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-slate-500 hover:bg-slate-100 hover:text-slate-900"
            >
              <X className="h-3 w-3" />
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Row 2: priority chips */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="mr-1 font-semibold uppercase tracking-wider text-slate-400">
          Priority
        </span>
        {PRIORITY_OPTIONS.map((p) => (
          <FilterChip
            key={p}
            active={filters.priorities.has(p)}
            onClick={() => togglePriority(p)}
          >
            {p}
          </FilterChip>
        ))}

        <span className="ml-4 mr-1 font-semibold uppercase tracking-wider text-slate-400">
          Health
        </span>
        {HEALTH_OPTIONS.map((h) => (
          <FilterChip
            key={h}
            active={filters.healths.has(h)}
            onClick={() => toggleHealth(h)}
          >
            {HEALTH_LABEL[h]}
          </FilterChip>
        ))}

        {pmOptions.length > 0 && (
          <>
            <span className="ml-4 mr-1 font-semibold uppercase tracking-wider text-slate-400">
              PM
            </span>
            <select
              value={filters.pm ?? ""}
              onChange={(e) =>
                onChange({ ...filters, pm: e.target.value || null })
              }
              className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
            >
              <option value="">All</option>
              {pmOptions.map((pm) => (
                <option key={pm} value={pm}>
                  {pm}
                </option>
              ))}
            </select>
          </>
        )}
      </div>
    </div>
  );
}

function FilterChip({
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
      {active && <Check className="h-3 w-3" />}
      {children}
    </button>
  );
}
