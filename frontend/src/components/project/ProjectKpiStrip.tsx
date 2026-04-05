import { motion } from "framer-motion";
import { Clock, DollarSign, TrendingUp, Gauge } from "lucide-react";
import type { Project } from "@/types/project";
import { Card } from "@/components/ui/card";
import { currency, hours } from "@/lib/format";

export function ProjectKpiStrip({
  project,
  durationWeeks,
}: {
  project: Project;
  durationWeeks: number;
}) {
  const budget = project.budget ?? 0;
  const forecast = project.forecast_cost ?? 0;
  const actual = project.actual_cost ?? 0;
  const spendPct = budget > 0 ? actual / budget : 0;

  const items: Array<{
    label: string;
    value: string;
    sub?: string;
    icon: React.ReactNode;
  }> = [
    {
      label: "Est. hours",
      value: hours(project.est_hours),
      sub:
        durationWeeks > 0
          ? `over ${durationWeeks.toFixed(1)} weeks`
          : "no timeline set",
      icon: <Clock className="h-4 w-4" />,
    },
    {
      label: "Budget",
      value: budget > 0 ? currency(budget) : "—",
      sub: budget > 0 ? "approved" : "not set",
      icon: <DollarSign className="h-4 w-4" />,
    },
    {
      label: "Actual spend",
      value: currency(actual),
      sub:
        budget > 0
          ? `${(spendPct * 100).toFixed(0)}% of budget`
          : forecast > 0
            ? `forecast ${currency(forecast)}`
            : "",
      icon: <Gauge className="h-4 w-4" />,
    },
    {
      label: "Forecast",
      value: forecast > 0 ? currency(forecast) : "—",
      sub:
        budget > 0 && forecast > 0
          ? forecast > budget
            ? `${currency(forecast - budget)} over budget`
            : `${currency(budget - forecast)} under budget`
          : "",
      icon: <TrendingUp className="h-4 w-4" />,
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item, i) => (
        <motion.div
          key={item.label}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: i * 0.05 }}
        >
          <Card className="ring-1 ring-inset ring-slate-200">
            <div className="flex h-full flex-col p-5">
              <div className="flex items-start justify-between">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  {item.label}
                </div>
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                  {item.icon}
                </div>
              </div>
              <div className="mt-3 text-2xl font-bold tabular-nums text-slate-900">
                {item.value}
              </div>
              {item.sub && (
                <div className="mt-auto pt-2 text-xs text-slate-500">{item.sub}</div>
              )}
            </div>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
