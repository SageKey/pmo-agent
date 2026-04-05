import { useMemo, useState } from "react";
import { Plus } from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { Button } from "@/components/ui/button";
import { type SortState } from "@/components/portfolio/ProjectTable";
import { ProjectGroup } from "@/components/portfolio/ProjectGroup";
import { NewProjectDialog } from "@/components/portfolio/NewProjectDialog";
import {
  PortfolioToolbar,
  type PortfolioFilters,
} from "@/components/portfolio/PortfolioToolbar";
import { usePortfolio } from "@/hooks/usePortfolio";
import type { Project } from "@/types/project";

const PRIORITY_ORDER: Record<string, number> = {
  Highest: 0,
  High: 1,
  Medium: 2,
  Low: 3,
};

function normalizeHealth(h: string | null): string {
  if (!h) return "";
  const up = h.toUpperCase();
  if (up.includes("ON TRACK")) return "ON TRACK";
  if (up.includes("AT RISK")) return "AT RISK";
  if (up.includes("NEEDS HELP")) return "NEEDS HELP";
  if (up.includes("NEEDS") && up.includes("SPEC")) return "NEEDS SPEC";
  if (up.includes("NOT STARTED")) return "NOT STARTED";
  if (up.includes("COMPLETE")) return "COMPLETE";
  if (up.includes("POSTPONED")) return "POSTPONED";
  return up;
}

function cmp<T>(a: T, b: T): number {
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b));
}

function sortProjects(projects: Project[], sort: SortState): Project[] {
  const out = [...projects];
  out.sort((a, b) => {
    let result = 0;
    switch (sort.key) {
      case "id":
        result = cmp(a.id, b.id);
        break;
      case "name":
        result = cmp(a.name, b.name);
        break;
      case "priority":
        result = cmp(
          PRIORITY_ORDER[a.priority ?? "Low"] ?? 99,
          PRIORITY_ORDER[b.priority ?? "Low"] ?? 99,
        );
        break;
      case "health":
        result = cmp(normalizeHealth(a.health), normalizeHealth(b.health));
        break;
      case "pct_complete":
        result = cmp(a.pct_complete, b.pct_complete);
        break;
      case "est_hours":
        result = cmp(a.est_hours, b.est_hours);
        break;
      case "start_date":
        result = cmp(a.start_date, b.start_date);
        break;
      case "end_date":
        result = cmp(a.end_date, b.end_date);
        break;
      case "pm":
        result = cmp(a.pm, b.pm);
        break;
    }
    return sort.dir === "asc" ? result : -result;
  });
  return out;
}

function isArchived(p: Project): boolean {
  // Archive = Complete OR Postponed. Everything else is "in flight" — even
  // "Not started" or "Needs spec", because they still consume future capacity.
  if (!p.is_active) return true;
  const h = normalizeHealth(p.health);
  return h === "COMPLETE" || h === "POSTPONED";
}

export function Portfolio() {
  const [filters, setFilters] = useState<PortfolioFilters>({
    search: "",
    priorities: new Set(),
    healths: new Set(),
    pm: null,
  });
  const [sort, setSort] = useState<SortState>({ key: "priority", dir: "asc" });
  const [archiveManualExpanded, setArchiveManualExpanded] = useState(false);
  const [inFlightExpanded, setInFlightExpanded] = useState(true);
  const [newOpen, setNewOpen] = useState(false);

  // Always fetch the full portfolio; grouping happens client-side.
  const { data, isLoading, isError, error } = usePortfolio(false);

  const pmOptions = useMemo(() => {
    const set = new Set<string>();
    (data ?? []).forEach((p) => {
      if (p.pm) set.add(p.pm);
    });
    return Array.from(set).sort();
  }, [data]);

  // Apply filters (search + chips) to the full list, then split into groups.
  const filtered = useMemo(() => {
    if (!data) return [];
    const q = filters.search.trim().toLowerCase();
    return data.filter((p) => {
      if (q) {
        const hay = `${p.id} ${p.name} ${p.pm ?? ""} ${p.portfolio ?? ""}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      if (filters.priorities.size > 0 && !filters.priorities.has(p.priority ?? "")) {
        return false;
      }
      if (filters.healths.size > 0) {
        if (!filters.healths.has(normalizeHealth(p.health))) return false;
      }
      if (filters.pm && p.pm !== filters.pm) return false;
      return true;
    });
  }, [data, filters]);

  const { inFlight, archive, archiveComplete, archivePostponed } = useMemo(() => {
    const flight: Project[] = [];
    const arch: Project[] = [];
    let complete = 0;
    let postponed = 0;
    for (const p of filtered) {
      if (isArchived(p)) {
        arch.push(p);
        if (normalizeHealth(p.health) === "POSTPONED") postponed++;
        else complete++;
      } else {
        flight.push(p);
      }
    }
    return {
      inFlight: sortProjects(flight, sort),
      archive: sortProjects(arch, sort),
      archiveComplete: complete,
      archivePostponed: postponed,
    };
  }, [filtered, sort]);

  // Unfiltered totals for the Archive header when no filter is active.
  const { archiveTotalCount, archiveTotalComplete, archiveTotalPostponed } =
    useMemo(() => {
      let total = 0;
      let complete = 0;
      let postponed = 0;
      for (const p of data ?? []) {
        if (isArchived(p)) {
          total++;
          if (normalizeHealth(p.health) === "POSTPONED") postponed++;
          else complete++;
        }
      }
      return {
        archiveTotalCount: total,
        archiveTotalComplete: complete,
        archiveTotalPostponed: postponed,
      };
    }, [data]);

  const anyFilterActive =
    filters.search !== "" ||
    filters.priorities.size > 0 ||
    filters.healths.size > 0 ||
    filters.pm !== null;

  // Auto-expand archive when a filter/search matches archived rows.
  const archiveExpanded =
    anyFilterActive && archive.length > 0 ? true : archiveManualExpanded;

  const archiveSubtitle = anyFilterActive
    ? `${archiveComplete} complete · ${archivePostponed} postponed`
    : `${archiveTotalComplete} complete · ${archiveTotalPostponed} postponed`;

  const archiveCount = anyFilterActive ? archive.length : archiveTotalCount;
  const archiveMatchBadge =
    anyFilterActive && archive.length > 0
      ? `${archive.length} match${archive.length === 1 ? "" : "es"}`
      : undefined;

  const totalMatched = filtered.length;

  return (
    <>
      <TopBar
        title="Portfolio"
        subtitle="Everything in flight, with archived work one click away."
      />
      <div className="space-y-5 p-8">
        <div className="flex items-center justify-between">
          <div />
          <Button onClick={() => setNewOpen(true)}>
            <Plus className="h-4 w-4" />
            New project
          </Button>
        </div>
        <PortfolioToolbar
          filters={filters}
          onChange={setFilters}
          pmOptions={pmOptions}
          totalMatched={totalMatched}
          totalAll={data?.length ?? 0}
        />

        {isLoading && (
          <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-500">
            Loading projects…
          </div>
        )}
        {isError && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-800">
            Failed to load: {(error as Error).message}
          </div>
        )}

        {data && (
          <div className="space-y-4">
            <ProjectGroup
              title="In flight"
              subtitle="active, not started, needs spec"
              count={inFlight.length}
              projects={inFlight}
              sort={sort}
              onSortChange={setSort}
              expanded={inFlightExpanded}
              onToggle={() => setInFlightExpanded((x) => !x)}
            />

            {archiveTotalCount > 0 && (
              <ProjectGroup
                title="Archive"
                subtitle={archiveSubtitle}
                count={archiveCount}
                projects={archive}
                sort={sort}
                onSortChange={setSort}
                expanded={archiveExpanded}
                onToggle={() => setArchiveManualExpanded((x) => !x)}
                matchBadge={archiveMatchBadge}
                muted
              />
            )}
          </div>
        )}
      </div>

      <NewProjectDialog open={newOpen} onOpenChange={setNewOpen} />
    </>
  );
}
