import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Plus, Search, Trash2 } from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { LogEntryDialog } from "@/components/timesheets/LogEntryDialog";
import {
  useDeleteTimesheetEntry,
  useTimesheetEntries,
  useTimesheetSummary,
} from "@/hooks/useTimesheets";
import { avatarTone, currency, initials, shortDate } from "@/lib/format";
import { cn } from "@/lib/cn";

function currentMonth(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function monthLabel(ym: string): string {
  const [y, m] = ym.split("-").map(Number);
  return `${String(m).padStart(2, "0")}-${y}`;
}

function prevMonth(ym: string): string {
  const [y, m] = ym.split("-").map(Number);
  const d = new Date(y, m - 2, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function nextMonth(ym: string): string {
  const [y, m] = ym.split("-").map(Number);
  const d = new Date(y, m, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function Timesheets() {
  const [month, setMonth] = useState<string>(currentMonth());
  const [search, setSearch] = useState("");
  const [logOpen, setLogOpen] = useState(false);

  const summary = useTimesheetSummary({ month });
  const entries = useTimesheetEntries({ month });
  const deleteMutation = useDeleteTimesheetEntry();

  const rows = summary.data ?? [];
  const totalHours = rows.reduce((s, r) => s + r.total_hours, 0);
  const projectHours = rows.reduce((s, r) => s + r.project_hours, 0);
  const supportHours = rows.reduce((s, r) => s + r.support_hours, 0);
  const tmCost = rows.reduce((s, r) => s + r.tm_cost, 0);

  const filteredEntries = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return entries.data ?? [];
    return (entries.data ?? []).filter((e) =>
      `${e.consultant_name ?? ""} ${e.project_key ?? ""} ${e.project_name ?? ""} ${e.task_description ?? ""}`
        .toLowerCase()
        .includes(q),
    );
  }, [entries.data, search]);

  return (
    <>
      <TopBar
        title="Timesheets"
        subtitle="Vendor consultant hours by month with project/support split."
      />
      <div className="space-y-6 p-8">
        {/* Month picker */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => setMonth(prevMonth(month))}
            className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
          >
            ← Prev
          </button>
          <div className="min-w-[180px] text-center text-sm font-semibold text-slate-900">
            {monthLabel(month)}
          </div>
          <button
            onClick={() => setMonth(nextMonth(month))}
            className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
          >
            Next →
          </button>
          <button
            onClick={() => setMonth(currentMonth())}
            className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
          >
            This month
          </button>
          <div className="ml-auto flex items-center gap-3 text-xs text-slate-500">
            <span>
              {rows.length} consultants · {filteredEntries.length} entries
            </span>
            <Button size="sm" onClick={() => setLogOpen(true)}>
              <Plus className="h-3.5 w-3.5" />
              Log entry
            </Button>
          </div>
        </div>

        {/* KPI row */}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Kpi label="Total hours" value={totalHours.toFixed(0)} />
          <Kpi
            label="Project hours"
            value={projectHours.toFixed(0)}
            sub={
              totalHours > 0
                ? `${((projectHours / totalHours) * 100).toFixed(0)}% of month`
                : ""
            }
          />
          <Kpi
            label="Support hours"
            value={supportHours.toFixed(0)}
            sub={
              totalHours > 0
                ? `${((supportHours / totalHours) * 100).toFixed(0)}% of month`
                : ""
            }
          />
          <Kpi label="T&M cost" value={currency(tmCost)} sub="Billable hourly" />
        </div>

        {/* Summary per consultant */}
        <Card>
          <CardHeader>
            <CardTitle>Consultant summary · {monthLabel(month)}</CardTitle>
          </CardHeader>
          <CardContent className="px-0 pb-0">
            {rows.length === 0 ? (
              <div className="py-10 text-center text-sm text-slate-500">
                No timesheet entries for {monthLabel(month)}.
              </div>
            ) : (
              <Table>
                <THead>
                  <TR>
                    <TH>Consultant</TH>
                    <TH>Type</TH>
                    <TH className="text-right">Rate</TH>
                    <TH className="text-right">Project</TH>
                    <TH className="text-right">Support</TH>
                    <TH className="text-right">Total</TH>
                    <TH>Split</TH>
                    <TH className="text-right">T&M cost</TH>
                  </TR>
                </THead>
                <TBody>
                  {rows
                    .slice()
                    .sort((a, b) => b.total_hours - a.total_hours)
                    .map((r, i) => {
                      const total = r.total_hours || 1;
                      return (
                        <motion.tr
                          key={r.consultant_id}
                          initial={{ opacity: 0, y: 3 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.25, delay: i * 0.02 }}
                          className="border-b border-slate-100 hover:bg-slate-50/60"
                        >
                          <TD>
                            <div className="flex items-center gap-2">
                              <div
                                className={cn(
                                  "flex h-7 w-7 items-center justify-center rounded-full text-[10px] font-semibold",
                                  avatarTone(r.name),
                                )}
                              >
                                {initials(r.name)}
                              </div>
                              <span className="text-sm font-medium text-slate-900">
                                {r.name}
                              </span>
                            </div>
                          </TD>
                          <TD className="whitespace-nowrap">
                            <span
                              className={cn(
                                "inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ring-1 ring-inset",
                                r.billing_type === "T&M"
                                  ? "bg-sky-50 text-sky-700 ring-sky-200"
                                  : "bg-navy-50 text-navy-700 ring-navy-200",
                              )}
                            >
                              {r.billing_type ?? "—"}
                            </span>
                          </TD>
                          <TD className="whitespace-nowrap text-right tabular-nums text-slate-600">
                            {r.hourly_rate ? `$${r.hourly_rate.toFixed(0)}/h` : "—"}
                          </TD>
                          <TD className="whitespace-nowrap text-right tabular-nums text-slate-700">
                            {r.project_hours.toFixed(0)}
                          </TD>
                          <TD className="whitespace-nowrap text-right tabular-nums text-slate-700">
                            {r.support_hours.toFixed(0)}
                          </TD>
                          <TD className="whitespace-nowrap text-right tabular-nums font-semibold text-slate-900">
                            {r.total_hours.toFixed(0)}
                          </TD>
                          <TD className="w-40">
                            <div className="flex h-2 w-36 overflow-hidden rounded-full bg-slate-100">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{
                                  width: `${(r.project_hours / total) * 100}%`,
                                }}
                                transition={{ duration: 0.5, delay: 0.15 + i * 0.02 }}
                                className="h-full bg-emerald-500"
                                title={`Project: ${r.project_hours}h`}
                              />
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{
                                  width: `${(r.support_hours / total) * 100}%`,
                                }}
                                transition={{ duration: 0.5, delay: 0.2 + i * 0.02 }}
                                className="h-full bg-amber-400"
                                title={`Support: ${r.support_hours}h`}
                              />
                            </div>
                          </TD>
                          <TD className="whitespace-nowrap text-right tabular-nums text-slate-900">
                            {r.billing_type === "T&M" && r.tm_cost > 0
                              ? currency(r.tm_cost)
                              : "—"}
                          </TD>
                        </motion.tr>
                      );
                    })}
                </TBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Entries table */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Entries</CardTitle>
              <div className="relative w-64">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
                <input
                  type="search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search entries…"
                  className="w-full rounded-md border border-slate-200 bg-slate-50 py-1.5 pl-8 pr-3 text-xs text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-navy-100"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent className="px-0 pb-0">
            {filteredEntries.length === 0 ? (
              <div className="py-10 text-center text-sm text-slate-500">
                {entries.data?.length === 0
                  ? "No entries for this month."
                  : "No entries match the search."}
              </div>
            ) : (
              <Table>
                <THead>
                  <TR>
                    <TH>Date</TH>
                    <TH>Consultant</TH>
                    <TH>Project</TH>
                    <TH>Task</TH>
                    <TH>Type</TH>
                    <TH className="text-right">Hrs</TH>
                    <TH className="w-10"></TH>
                  </TR>
                </THead>
                <TBody>
                  {filteredEntries
                    .slice()
                    .sort((a, b) => b.entry_date.localeCompare(a.entry_date))
                    .slice(0, 200)
                    .map((e) => (
                      <TR key={e.id} className="group">
                        <TD className="whitespace-nowrap text-slate-600">
                          {shortDate(e.entry_date)}
                        </TD>
                        <TD className="whitespace-nowrap text-slate-800">
                          {e.consultant_name ?? "—"}
                        </TD>
                        <TD className="whitespace-nowrap">
                          {e.project_key && (
                            <span className="mr-1 rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] font-medium text-slate-600">
                              {e.project_key}
                            </span>
                          )}
                          <span className="text-xs text-slate-600">
                            {e.project_name ?? ""}
                          </span>
                        </TD>
                        <TD className="max-w-[280px] truncate text-xs text-slate-600">
                          {e.task_description ?? "—"}
                        </TD>
                        <TD>
                          <span
                            className={cn(
                              "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium",
                              e.work_type === "Project"
                                ? "bg-emerald-50 text-emerald-700"
                                : "bg-amber-50 text-amber-700",
                            )}
                          >
                            {e.work_type ?? "—"}
                          </span>
                        </TD>
                        <TD className="whitespace-nowrap text-right tabular-nums text-slate-700">
                          {e.hours.toFixed(1)}
                        </TD>
                        <TD>
                          <button
                            onClick={() => {
                              if (confirm("Delete this entry?")) {
                                deleteMutation.mutate(e.id);
                              }
                            }}
                            disabled={deleteMutation.isPending}
                            className="rounded p-1 text-slate-300 opacity-0 transition-all hover:bg-red-50 hover:text-red-600 group-hover:opacity-100"
                            title="Delete entry"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </TD>
                      </TR>
                    ))}
                </TBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      <LogEntryDialog
        defaultMonth={month}
        open={logOpen}
        onOpenChange={setLogOpen}
      />
    </>
  );
}

function Kpi({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <Card className="ring-1 ring-inset ring-slate-200">
      <div className="flex h-full flex-col p-5">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          {label}
        </div>
        <div className="mt-3 text-2xl font-bold tabular-nums text-slate-900">
          {value}
        </div>
        {sub && <div className="mt-auto pt-2 text-xs text-slate-500">{sub}</div>}
      </div>
    </Card>
  );
}
