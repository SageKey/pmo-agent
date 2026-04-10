import { motion } from "framer-motion";
import {
  AlertCircle,
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  CheckCircle2,
  Minus,
  TrendingDown,
  UserX,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/cn";
import { pct } from "@/lib/format";
import type { ScenarioEvaluateResponse } from "@/types/scenario";

const ROLE_LABEL: Record<string, string> = {
  pm: "PM",
  ba: "BA",
  functional: "Functional",
  technical: "Technical",
  developer: "Developer",
  infrastructure: "Infrastructure",
  dba: "DBA",
  erp: "ERP",
};

const STATUS_DOT: Record<string, string> = {
  BLUE: "bg-sky-500",
  GREEN: "bg-emerald-500",
  YELLOW: "bg-amber-500",
  RED: "bg-red-500",
  GREY: "bg-slate-400",
};

const STATUS_BAR: Record<string, string> = {
  BLUE: "bg-sky-500",
  GREEN: "bg-emerald-500",
  YELLOW: "bg-amber-500",
  RED: "bg-red-500",
  GREY: "bg-slate-400",
};

export function ScenarioComparison({
  result,
  isPending,
  hasModifications,
}: {
  result: ScenarioEvaluateResponse | undefined;
  isPending: boolean;
  hasModifications: boolean;
}) {
  if (!result) {
    return (
      <Card className="flex items-center justify-center py-24 text-sm text-slate-500">
        {isPending
          ? "Running scenario…"
          : hasModifications
            ? "Click Evaluate to see the impact"
            : "Add modifications on the left, then evaluate to see the before/after."}
      </Card>
    );
  }

  const { summary, deltas, baseline, scenario } = result;

  // Sort deltas by absolute change descending so the most impactful rows
  // bubble to the top — matches what an executive wants to see first.
  const sortedDeltas = [...deltas].sort(
    (a, b) => Math.abs(b.delta_pct) - Math.abs(a.delta_pct),
  );

  // Derive banner tone from the summary. Precedence matches the engine:
  // over > unstaffed > stretched > better > neutral.
  const tone =
    summary.became_over.length > 0
      ? "danger"
      : summary.became_unstaffed.length > 0
        ? "neutral"
        : summary.became_stretched.length > 0
          ? "warning"
          : summary.became_better.length > 0
            ? "success"
            : "info";

  const BannerIcon = {
    danger: AlertCircle,
    warning: AlertTriangle,
    neutral: UserX,
    success: CheckCircle2,
    info: TrendingDown,
  }[tone];

  const bannerTone = {
    danger: "from-red-50 to-white ring-red-200 text-red-800",
    warning: "from-amber-50 to-white ring-amber-200 text-amber-800",
    neutral: "from-slate-100 to-white ring-slate-300 text-slate-800",
    success: "from-emerald-50 to-white ring-emerald-200 text-emerald-800",
    info: "from-sky-50 to-white ring-sky-200 text-sky-800",
  }[tone];

  return (
    <div className="space-y-4">
      {/* Headline banner */}
      <motion.div
        key={summary.headline}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        <Card className="overflow-hidden ring-1 ring-inset ring-slate-200">
          <div
            className={cn(
              "flex items-start gap-4 bg-gradient-to-r px-6 py-5 ring-1 ring-inset",
              bannerTone,
            )}
          >
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/70 ring-1 ring-inset ring-white">
              <BannerIcon className="h-6 w-6" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-lg font-semibold tracking-tight">
                {summary.headline}
              </div>
              <BreakdownLine summary={summary} />
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Role-by-role before/after */}
      <Card>
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-3">
          <div className="text-sm font-semibold text-slate-700">
            Role impact
          </div>
          <div className="flex items-center gap-4 text-[11px] uppercase tracking-wider text-slate-400">
            <span>Baseline</span>
            <span>→</span>
            <span>Scenario</span>
          </div>
        </div>
        <div className="divide-y divide-slate-100">
          {sortedDeltas.map((d, i) => {
            const b = baseline.roles[d.role_key];
            const s = scenario.roles[d.role_key];
            return (
              <DeltaRow
                key={d.role_key}
                roleLabel={ROLE_LABEL[d.role_key] ?? d.role_key}
                baseline={b}
                scenario={s}
                deltaPct={d.delta_pct}
                statusChanged={d.status_changed}
                delay={i * 0.04}
              />
            );
          })}
        </div>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------

function BreakdownLine({
  summary,
}: {
  summary: ScenarioEvaluateResponse["summary"];
}) {
  const parts: string[] = [];
  if (summary.became_over.length)
    parts.push(
      `${summary.became_over.length} → over: ${summary.became_over
        .map((k) => ROLE_LABEL[k] ?? k)
        .join(", ")}`,
    );
  if (summary.became_unstaffed.length)
    parts.push(
      `${summary.became_unstaffed.length} → unstaffed: ${summary.became_unstaffed
        .map((k) => ROLE_LABEL[k] ?? k)
        .join(", ")}`,
    );
  if (summary.became_stretched.length)
    parts.push(
      `${summary.became_stretched.length} → stretched: ${summary.became_stretched
        .map((k) => ROLE_LABEL[k] ?? k)
        .join(", ")}`,
    );
  if (summary.became_better.length)
    parts.push(
      `${summary.became_better.length} freed up: ${summary.became_better
        .map((k) => ROLE_LABEL[k] ?? k)
        .join(", ")}`,
    );
  if (!parts.length) return null;
  return (
    <div className="mt-0.5 text-sm opacity-80">{parts.join(" · ")}</div>
  );
}

function DeltaRow({
  roleLabel,
  baseline,
  scenario,
  deltaPct,
  statusChanged,
  delay,
}: {
  roleLabel: string;
  baseline: ScenarioEvaluateResponse["baseline"]["roles"][string];
  scenario: ScenarioEvaluateResponse["scenario"]["roles"][string];
  deltaPct: number;
  statusChanged: boolean;
  delay: number;
}) {
  const baselineUnstaffed = baseline.status === "GREY";
  const scenarioUnstaffed = scenario.status === "GREY";
  const baseWidth = baselineUnstaffed
    ? 100
    : Math.min(baseline.utilization_pct, 1.25) * 100;
  const scenWidth = scenarioUnstaffed
    ? 100
    : Math.min(scenario.utilization_pct, 1.25) * 100;

  const direction = deltaPct > 0.005 ? "up" : deltaPct < -0.005 ? "down" : "flat";
  const DeltaIcon =
    direction === "up" ? ArrowUp : direction === "down" ? ArrowDown : Minus;
  const deltaColor =
    direction === "up"
      ? "text-red-600"
      : direction === "down"
        ? "text-emerald-600"
        : "text-slate-400";

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay }}
      className={cn(
        "grid grid-cols-12 items-center gap-3 px-6 py-3",
        statusChanged && "bg-slate-50",
      )}
    >
      <div className="col-span-2 flex items-center gap-2">
        <span className="text-sm font-medium text-slate-800">{roleLabel}</span>
      </div>

      {/* Baseline bar */}
      <div className="col-span-4 space-y-1">
        <div
          className={cn(
            "h-2 overflow-hidden rounded-full bg-slate-100",
            baselineUnstaffed &&
              "bg-[repeating-linear-gradient(45deg,#e2e8f0_0_6px,#f1f5f9_6px_12px)]",
          )}
        >
          {!baselineUnstaffed && (
            <div
              className={cn("h-full rounded-full", STATUS_BAR[baseline.status])}
              style={{ width: `${baseWidth}%` }}
            />
          )}
        </div>
        <div className="flex items-center gap-2 text-[11px] text-slate-500 tabular-nums">
          <span
            className={cn("h-1.5 w-1.5 rounded-full", STATUS_DOT[baseline.status])}
          />
          <span className="font-semibold">
            {baselineUnstaffed ? "Unstaffed" : pct(baseline.utilization_pct)}
          </span>
          <span>·</span>
          <span>{baseline.demand_hrs_week.toFixed(0)} / {baseline.supply_hrs_week.toFixed(0)} hrs</span>
        </div>
      </div>

      {/* Delta indicator */}
      <div className="col-span-2 text-center">
        <div className={cn("inline-flex items-center gap-1 text-sm font-semibold tabular-nums", deltaColor)}>
          <DeltaIcon className="h-3.5 w-3.5" />
          {direction === "flat"
            ? "no change"
            : `${deltaPct >= 0 ? "+" : ""}${(deltaPct * 100).toFixed(0)}pp`}
        </div>
        {statusChanged && (
          <div className="mt-0.5 text-[10px] font-medium uppercase tracking-wider text-slate-400">
            status change
          </div>
        )}
      </div>

      {/* Scenario bar */}
      <div className="col-span-4 space-y-1">
        <motion.div
          className={cn(
            "h-2 overflow-hidden rounded-full bg-slate-100",
            scenarioUnstaffed &&
              "bg-[repeating-linear-gradient(45deg,#e2e8f0_0_6px,#f1f5f9_6px_12px)]",
          )}
        >
          {!scenarioUnstaffed && (
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${scenWidth}%` }}
              transition={{ duration: 0.5, delay: delay + 0.1, ease: "easeOut" }}
              className={cn("h-full rounded-full", STATUS_BAR[scenario.status])}
            />
          )}
        </motion.div>
        <div className="flex items-center gap-2 text-[11px] text-slate-500 tabular-nums">
          <span
            className={cn("h-1.5 w-1.5 rounded-full", STATUS_DOT[scenario.status])}
          />
          <span className="font-semibold">
            {scenarioUnstaffed ? "Unstaffed" : pct(scenario.utilization_pct)}
          </span>
          <span>·</span>
          <span>{scenario.demand_hrs_week.toFixed(0)} / {scenario.supply_hrs_week.toFixed(0)} hrs</span>
        </div>
      </div>
    </motion.div>
  );
}
