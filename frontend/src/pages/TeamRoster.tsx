import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Plus, Search } from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { Button } from "@/components/ui/button";
import { PersonCard } from "@/components/roster/PersonCard";
import { PersonDetailDrawer } from "@/components/roster/PersonDetailDrawer";
import { EditMemberDialog } from "@/components/roster/EditMemberDialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { usePersonAvailability, usePersonDemand, useRoster } from "@/hooks/useRoster";
import type { PersonAvailability, PersonDemand, TeamMember } from "@/types/roster";
import { cn } from "@/lib/cn";

const ROLE_LABEL: Record<string, string> = {
  pm: "Project Manager",
  ba: "Business Analyst",
  functional: "Functional",
  technical: "Technical",
  developer: "Developer",
  infrastructure: "Infrastructure",
  dba: "DBA",
  erp: "ERP",
};

const ROLE_ORDER = [
  "pm",
  "ba",
  "functional",
  "technical",
  "developer",
  "infrastructure",
  "dba",
  "erp",
];

export function TeamRoster() {
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<string | null>(null);
  const [selected, setSelected] = useState<PersonDemand | null>(null);
  const [editMember, setEditMember] = useState<TeamMember | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data, isLoading, isError, error } = usePersonDemand();
  const rosterQuery = useRoster();
  const roster = rosterQuery.data ?? [];
  const availQuery = usePersonAvailability();
  const availByName = useMemo(() => {
    const map = new Map<string, PersonAvailability>();
    for (const a of availQuery.data ?? []) map.set(a.name, a);
    return map;
  }, [availQuery.data]);

  const openEdit = (m: TeamMember) => {
    setEditMember(m);
    setDialogOpen(true);
    setSelected(null); // close the drawer so it doesn't stack
  };
  const openNew = () => {
    setEditMember(null);
    setDialogOpen(true);
  };

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = search.trim().toLowerCase();
    return data.filter((p) => {
      if (q && !`${p.name} ${p.role}`.toLowerCase().includes(q)) return false;
      if (roleFilter && p.role_key !== roleFilter) return false;
      return true;
    });
  }, [data, search, roleFilter]);

  // Group by role, preserving role order
  const grouped = useMemo(() => {
    const byRole = new Map<string, PersonDemand[]>();
    for (const p of filtered) {
      if (!byRole.has(p.role_key)) byRole.set(p.role_key, []);
      byRole.get(p.role_key)!.push(p);
    }
    // Sort each group by utilization desc
    for (const arr of byRole.values()) {
      arr.sort((a, b) => b.utilization_pct - a.utilization_pct);
    }
    return ROLE_ORDER.filter((r) => byRole.has(r)).map((r) => ({
      role_key: r,
      members: byRole.get(r)!,
    }));
  }, [filtered]);

  // Role counts for filter pills (from unfiltered data)
  const roleCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const p of data ?? []) {
      counts[p.role_key] = (counts[p.role_key] ?? 0) + 1;
    }
    return counts;
  }, [data]);

  // Topline: who's red, who's most available? Only counted members — the
  // excluded ones are shown on the roster but explicitly don't participate
  // in capacity math, so they shouldn't affect overload/availability stats.
  const countedPeople = (data ?? []).filter((p) => p.include_in_capacity);
  const excludedCount = (data ?? []).length - countedPeople.length;
  const redPeople = countedPeople.filter((p) => p.status === "RED");
  // "Most available" includes both BLUE (under-utilized) and GREEN (ideal)
  // members sorted by utilization ascending so the lightest-loaded surface first.
  const availablePeople = countedPeople
    .filter((p) => p.status === "BLUE" || p.status === "GREEN")
    .sort((a, b) => a.utilization_pct - b.utilization_pct)
    .slice(0, 5);

  return (
    <>
      <TopBar
        title="Team Roster"
        subtitle="Person-level load across the 8 IT roles."
      />
      <div className="space-y-6 p-8">
        <div className="flex items-center justify-between">
          <div />
          <Button onClick={openNew}>
            <Plus className="h-4 w-4" />
            New member
          </Button>
        </div>
        {/* Topline: overloaded + most available */}
        {data && (
          <div className="grid gap-4 md:grid-cols-2">
            <Card
              className={cn(
                "ring-1 ring-inset",
                redPeople.length > 0 ? "ring-red-200" : "ring-emerald-200",
              )}
            >
              <CardHeader>
                <CardTitle>
                  {redPeople.length > 0
                    ? `${redPeople.length} overloaded`
                    : "No one overloaded"}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {redPeople.length > 0 ? (
                  <ul className="space-y-2">
                    {redPeople.slice(0, 5).map((p) => (
                      <li
                        key={p.name}
                        className="flex items-center justify-between text-sm"
                      >
                        <button
                          onClick={() => setSelected(p)}
                          className="text-left font-medium text-slate-900 hover:text-navy-700"
                        >
                          {p.name}
                        </button>
                        <span className="tabular-nums text-red-700">
                          {(p.utilization_pct * 100).toFixed(0)}% · {p.project_count} proj
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-sm text-slate-500">
                    Every team member is under 100% utilization.
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="ring-1 ring-inset ring-slate-200">
              <CardHeader>
                <CardTitle>Most available</CardTitle>
              </CardHeader>
              <CardContent>
                {availablePeople.length > 0 ? (
                  <ul className="space-y-2">
                    {availablePeople.map((p) => (
                      <li
                        key={p.name}
                        className="flex items-center justify-between text-sm"
                      >
                        <button
                          onClick={() => setSelected(p)}
                          className="text-left font-medium text-slate-900 hover:text-navy-700"
                        >
                          {p.name}
                        </button>
                        <span className="tabular-nums text-emerald-700">
                          {(p.utilization_pct * 100).toFixed(0)}% · {p.project_count} proj
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-sm text-slate-500">
                    Nobody in the ideal band right now.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Toolbar */}
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-card"
        >
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative min-w-[240px] flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search team members…"
                className="w-full rounded-md border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
            </div>
            <div className="ml-auto text-xs text-slate-500 tabular-nums">
              <span className="font-semibold text-slate-900">{filtered.length}</span>{" "}
              of {data?.length ?? 0} team members
              {excludedCount > 0 && (
                <span className="ml-2 text-slate-400">
                  ({excludedCount} not counted)
                </span>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="mr-1 font-semibold uppercase tracking-wider text-slate-400">
              Role
            </span>
            <FilterChip active={roleFilter === null} onClick={() => setRoleFilter(null)}>
              All
            </FilterChip>
            {ROLE_ORDER.filter((r) => roleCounts[r]).map((r) => (
              <FilterChip
                key={r}
                active={roleFilter === r}
                onClick={() => setRoleFilter(roleFilter === r ? null : r)}
              >
                {ROLE_LABEL[r]} · {roleCounts[r]}
              </FilterChip>
            ))}
          </div>
        </motion.div>

        {isLoading && (
          <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-500">
            Loading team…
          </div>
        )}
        {isError && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-800">
            Failed to load: {(error as Error).message}
          </div>
        )}

        {/* Grouped person cards */}
        {grouped.map(({ role_key, members }, gi) => (
          <section key={role_key} className="space-y-3">
            <div className="flex items-baseline gap-2">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-900">
                {ROLE_LABEL[role_key] ?? role_key}
              </h2>
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold tabular-nums text-slate-600">
                {members.length}
              </span>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {members.map((p, i) => (
                <PersonCard
                  key={p.name}
                  person={p}
                  index={gi * 10 + i}
                  onClick={() => setSelected(p)}
                  availability={availByName.get(p.name)}
                />
              ))}
            </div>
          </section>
        ))}

        {grouped.length === 0 && !isLoading && data && (
          <div className="rounded-xl border border-dashed border-slate-200 bg-white p-12 text-center text-sm text-slate-500">
            No team members match the current filters.
          </div>
        )}
      </div>

      <PersonDetailDrawer
        person={selected}
        roster={roster}
        onClose={() => setSelected(null)}
        onEdit={openEdit}
      />

      <EditMemberDialog
        member={editMember}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
      />
    </>
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
      {children}
    </button>
  );
}
