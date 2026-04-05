import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { DollarSign, FileText, PieChart, TrendingUp } from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import {
  useInvoices,
  useMonthlyCosts,
  useProjectCosts,
  useVendors,
} from "@/hooks/useFinancials";
import { currency, shortDate } from "@/lib/format";
import { cn } from "@/lib/cn";

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

export function Financials() {
  const [year, setYear] = useState<number>(2026);
  const vendors = useVendors(true);
  const invoices = useInvoices(year);
  const monthly = useMonthlyCosts(year);
  const byProject = useProjectCosts(year);

  // Build a monthly bar data array [{month: "Jan", msa, tm, total}] for the year
  const monthlyBars = useMemo(() => {
    const rows: Record<string, { month: string; msa: number; tm: number }> = {};
    for (let i = 0; i < 12; i++) {
      const key = `${year}-${String(i + 1).padStart(2, "0")}`;
      rows[key] = { month: MONTHS[i], msa: 0, tm: 0 };
    }
    for (const r of monthly.data ?? []) {
      if (!rows[r.month]) continue;
      if (r.billing_type === "MSA") rows[r.month].msa += r.total_cost;
      else rows[r.month].tm += r.total_cost;
    }
    return Object.values(rows);
  }, [monthly.data, year]);

  const ytdTotal = monthlyBars.reduce((s, r) => s + r.msa + r.tm, 0);
  const ytdMsa = monthlyBars.reduce((s, r) => s + r.msa, 0);
  const ytdTm = monthlyBars.reduce((s, r) => s + r.tm, 0);
  const maxBar = Math.max(...monthlyBars.map((r) => r.msa + r.tm), 1);

  const unpaid = (invoices.data ?? []).filter((inv) => !inv.paid);
  const unpaidAmt = unpaid.reduce((s, inv) => s + inv.total_amount, 0);

  const topProjects = (byProject.data ?? [])
    .slice()
    .sort((a, b) => b.total_cost - a.total_cost)
    .slice(0, 10);

  return (
    <>
      <TopBar title="Financials" subtitle="Vendor spend, invoices, and per-project cost." />
      <div className="space-y-6 p-8">
        {/* Year selector */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Year
          </span>
          <div className="inline-flex overflow-hidden rounded-md border border-slate-200">
            {[2025, 2026, 2027].map((y) => (
              <button
                key={y}
                onClick={() => setYear(y)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium transition-colors",
                  year === y
                    ? "bg-navy-900 text-white"
                    : "bg-white text-slate-600 hover:bg-slate-50",
                  y !== 2025 && "border-l border-slate-200",
                )}
              >
                {y}
              </button>
            ))}
          </div>
          <div className="ml-auto text-xs text-slate-500">
            {vendors.data?.length ?? 0} active vendors · {invoices.data?.length ?? 0}{" "}
            invoices
          </div>
        </div>

        {/* KPI row */}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            label={`YTD spend · ${year}`}
            value={currency(ytdTotal)}
            sub={`${currency(ytdMsa)} MSA · ${currency(ytdTm)} T&M`}
            icon={<DollarSign className="h-4 w-4" />}
          />
          <KpiCard
            label="MSA retainer"
            value={currency(ytdMsa)}
            sub="Flat monthly fees"
            icon={<PieChart className="h-4 w-4" />}
          />
          <KpiCard
            label="T&M spend"
            value={currency(ytdTm)}
            sub="Hourly consultants"
            icon={<TrendingUp className="h-4 w-4" />}
          />
          <KpiCard
            label="Unpaid invoices"
            value={unpaid.length.toString()}
            sub={unpaid.length > 0 ? `${currency(unpaidAmt)} outstanding` : "all settled"}
            icon={<FileText className="h-4 w-4" />}
            tone={unpaid.length > 0 ? "warning" : "success"}
          />
        </div>

        {/* Monthly bars */}
        <Card>
          <CardHeader>
            <CardTitle>Vendor spend by month · {year}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-3">
              {monthlyBars.map((m, i) => {
                const total = m.msa + m.tm;
                const hPct = total > 0 ? (total / maxBar) * 100 : 0;
                const msaH = total > 0 ? (m.msa / total) * hPct : 0;
                const tmH = total > 0 ? (m.tm / total) * hPct : 0;
                return (
                  <div key={m.month} className="flex flex-1 flex-col items-center gap-1">
                    <div
                      className="relative flex w-full flex-col justify-end"
                      style={{ height: 140 }}
                    >
                      {total > 0 && (
                        <div className="absolute -top-5 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] font-semibold tabular-nums text-slate-700">
                          ${Math.round(total / 1000)}k
                        </div>
                      )}
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: `${tmH}%` }}
                        transition={{ duration: 0.5, delay: i * 0.03 }}
                        className="rounded-t bg-sky-500"
                        title={`T&M: ${currency(m.tm)}`}
                      />
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: `${msaH}%` }}
                        transition={{ duration: 0.5, delay: i * 0.03 + 0.1 }}
                        className="bg-navy-700"
                        title={`MSA: ${currency(m.msa)}`}
                      />
                    </div>
                    <div className="text-[11px] font-medium text-slate-500">
                      {m.month}
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="mt-5 flex items-center gap-5 border-t border-slate-100 pt-3 text-xs text-slate-500">
              <LegendItem color="bg-navy-700" label="MSA retainer" />
              <LegendItem color="bg-sky-500" label="T&M hourly" />
            </div>
          </CardContent>
        </Card>

        {/* Two-column: top projects + invoices */}
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Top 10 projects by spend · {year}</CardTitle>
            </CardHeader>
            <CardContent className="px-0 pb-0">
              {topProjects.length === 0 ? (
                <div className="py-10 text-center text-sm text-slate-500">
                  No project cost data for {year}.
                </div>
              ) : (
                <Table>
                  <THead>
                    <TR>
                      <TH>Project</TH>
                      <TH className="text-right">Hours</TH>
                      <TH className="text-right">Cost</TH>
                    </TR>
                  </THead>
                  <TBody>
                    {topProjects.map((p) => (
                      <TR key={p.ete_project_id ?? p.ete_project_name ?? ""}>
                        <TD>
                          <div className="flex items-center gap-2">
                            {p.ete_project_id && (
                              <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] font-medium text-slate-600">
                                {p.ete_project_id}
                              </span>
                            )}
                            <span className="truncate text-sm text-slate-800">
                              {p.ete_project_name ?? "—"}
                            </span>
                          </div>
                        </TD>
                        <TD className="whitespace-nowrap text-right tabular-nums text-slate-600">
                          {p.total_hours.toFixed(0)}
                        </TD>
                        <TD className="whitespace-nowrap text-right tabular-nums font-medium text-slate-900">
                          {currency(p.total_cost)}
                        </TD>
                      </TR>
                    ))}
                  </TBody>
                </Table>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Invoices · {year}</CardTitle>
            </CardHeader>
            <CardContent className="px-0 pb-0">
              {(invoices.data ?? []).length === 0 ? (
                <div className="py-10 text-center text-sm text-slate-500">
                  No invoices for {year}.
                </div>
              ) : (
                <Table>
                  <THead>
                    <TR>
                      <TH>Month</TH>
                      <TH>Invoice #</TH>
                      <TH>Received</TH>
                      <TH className="text-right">Amount</TH>
                      <TH>Status</TH>
                    </TR>
                  </THead>
                  <TBody>
                    {(invoices.data ?? [])
                      .slice()
                      .sort((a, b) => b.month.localeCompare(a.month))
                      .map((inv) => (
                        <TR key={inv.id}>
                          <TD className="whitespace-nowrap font-medium">{inv.month}</TD>
                          <TD className="whitespace-nowrap text-xs text-slate-600">
                            {inv.invoice_number ?? "—"}
                          </TD>
                          <TD className="whitespace-nowrap text-xs text-slate-600">
                            {shortDate(inv.received_date)}
                          </TD>
                          <TD className="whitespace-nowrap text-right tabular-nums font-medium">
                            {currency(inv.total_amount)}
                          </TD>
                          <TD>
                            <span
                              className={cn(
                                "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset",
                                inv.paid
                                  ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
                                  : "bg-amber-50 text-amber-700 ring-amber-200",
                              )}
                            >
                              {inv.paid ? "Paid" : "Unpaid"}
                            </span>
                          </TD>
                        </TR>
                      ))}
                  </TBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}

function KpiCard({
  label,
  value,
  sub,
  icon,
  tone = "neutral",
}: {
  label: string;
  value: string;
  sub?: string;
  icon: React.ReactNode;
  tone?: "neutral" | "warning" | "success";
}) {
  const ring =
    tone === "warning"
      ? "ring-amber-200"
      : tone === "success"
        ? "ring-emerald-200"
        : "ring-slate-200";
  const iconBg =
    tone === "warning"
      ? "bg-amber-100 text-amber-700"
      : tone === "success"
        ? "bg-emerald-100 text-emerald-700"
        : "bg-slate-100 text-slate-600";
  return (
    <Card className={cn("ring-1 ring-inset", ring)}>
      <div className="flex h-full flex-col p-5">
        <div className="flex items-start justify-between">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            {label}
          </div>
          <div
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-lg",
              iconBg,
            )}
          >
            {icon}
          </div>
        </div>
        <div className="mt-3 text-2xl font-bold tabular-nums text-slate-900">
          {value}
        </div>
        {sub && <div className="mt-auto pt-2 text-xs text-slate-500">{sub}</div>}
      </div>
    </Card>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className={cn("h-3 w-4 rounded", color)} />
      <span>{label}</span>
    </div>
  );
}
