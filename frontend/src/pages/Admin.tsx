import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Check, Loader2, RotateCcw, Settings as SettingsIcon } from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useSettings, useUpdateSetting } from "@/hooks/useSettings";
import type { AppSetting } from "@/types/settings";
import { cn } from "@/lib/cn";

export function Admin() {
  const { data, isLoading, isError, error } = useSettings();
  const settings = data ?? [];

  // Group by category, preserving sort_order within a category.
  const grouped = useMemo(() => {
    const by = new Map<string, AppSetting[]>();
    for (const s of settings) {
      if (!by.has(s.category)) by.set(s.category, []);
      by.get(s.category)!.push(s);
    }
    for (const arr of by.values()) arr.sort((a, b) => a.sort_order - b.sort_order);
    return Array.from(by.entries());
  }, [settings]);

  return (
    <>
      <TopBar
        title="Admin Settings"
        subtitle="Configure thresholds and rules that drive the dashboards."
      />
      <div className="space-y-6 p-8">
        {isLoading && (
          <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-500">
            Loading settings…
          </div>
        )}
        {isError && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-800">
            Failed to load settings: {(error as Error).message}
          </div>
        )}

        {grouped.map(([category, rows]) => (
          <CategoryCard key={category} category={category} rows={rows} />
        ))}
      </div>
    </>
  );
}

// --- Category card ---------------------------------------------------------

function CategoryCard({
  category,
  rows,
}: {
  category: string;
  rows: AppSetting[];
}) {
  const title =
    category === "utilization"
      ? "Utilization Thresholds"
      : category[0].toUpperCase() + category.slice(1);
  const description =
    category === "utilization"
      ? "Controls when roles are flagged as under-utilized, ideal, stretched, or over capacity. Disable a state to collapse its range into the next band."
      : undefined;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
    >
      <Card className="overflow-hidden ring-1 ring-inset ring-slate-200">
        <CardHeader className="border-b border-slate-100">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 rounded-md bg-navy-50 p-2 text-navy-700">
              <SettingsIcon className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <CardTitle className="text-base">{title}</CardTitle>
              {description && (
                <p className="mt-1 text-sm text-slate-500">{description}</p>
              )}
            </div>
          </div>
        </CardHeader>

        {category === "utilization" && (
          <UtilizationPreview rows={rows} />
        )}

        <CardContent className="divide-y divide-slate-100 p-0">
          {rows.map((row) => (
            <SettingRow key={row.key} setting={row} />
          ))}
        </CardContent>
      </Card>
    </motion.div>
  );
}

// --- Threshold preview bar for the utilization category -------------------

function UtilizationPreview({ rows }: { rows: AppSetting[] }) {
  const byKey = Object.fromEntries(rows.map((r) => [r.key, r]));
  const num = (k: string, def: number) =>
    parseFloat(byKey[k]?.value ?? "") || def;
  const bool = (k: string, def: boolean) => {
    const v = byKey[k]?.value;
    if (v == null) return def;
    return v === "1" || v === "true";
  };

  const underMax = num("util_under_max", 0.7);
  const idealMax = num("util_ideal_max", 0.8);
  const stretchedMax = num("util_stretched_max", 1.0);
  const underOn = bool("util_under_enabled", true);
  const idealOn = bool("util_ideal_enabled", true);
  const stretchedOn = bool("util_stretched_enabled", true);
  const overOn = bool("util_over_enabled", true);

  // Show the bands between 0% and 150% (clamp display).
  const MAX = 1.5;
  const segments = [
    { key: "under", start: 0, end: underMax, on: underOn, color: "bg-sky-400", label: "Under" },
    { key: "ideal", start: underMax, end: idealMax, on: idealOn, color: "bg-emerald-400", label: "Ideal" },
    { key: "stretched", start: idealMax, end: stretchedMax, on: stretchedOn, color: "bg-amber-400", label: "Stretched" },
    { key: "over", start: stretchedMax, end: MAX, on: overOn, color: "bg-red-400", label: "Over" },
  ];

  return (
    <div className="border-b border-slate-100 bg-slate-50 px-6 py-5">
      <div className="mb-2 flex items-baseline justify-between">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Live preview
        </div>
        <div className="text-[11px] text-slate-400 tabular-nums">0% — 150%</div>
      </div>
      <div className="flex h-6 w-full overflow-hidden rounded-md ring-1 ring-inset ring-slate-200">
        {segments.map((s) => {
          const w = Math.max(0, (s.end - s.start) / MAX) * 100;
          if (w <= 0) return null;
          return (
            <div
              key={s.key}
              style={{ width: `${w}%` }}
              className={cn(
                "relative flex items-center justify-center",
                s.on ? s.color : "bg-slate-200",
              )}
              title={
                s.on
                  ? `${s.label}: ${(s.start * 100).toFixed(0)}–${(s.end * 100).toFixed(0)}%`
                  : `${s.label} (disabled)`
              }
            >
              {w > 12 && (
                <span
                  className={cn(
                    "px-1 text-[10px] font-semibold uppercase tracking-wider",
                    s.on ? "text-white/90" : "text-slate-400 line-through",
                  )}
                >
                  {s.label}
                </span>
              )}
            </div>
          );
        })}
      </div>
      <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500 tabular-nums">
        <span>0%</span>
        <span>{Math.round(underMax * 100)}%</span>
        <span>{Math.round(idealMax * 100)}%</span>
        <span>{Math.round(stretchedMax * 100)}%</span>
        <span>150%</span>
      </div>
    </div>
  );
}

// --- Single setting row ----------------------------------------------------

function SettingRow({ setting }: { setting: AppSetting }) {
  const mutation = useUpdateSetting();
  const [draft, setDraft] = useState(setting.value);
  const [savedFlash, setSavedFlash] = useState(false);

  useEffect(() => {
    setDraft(setting.value);
  }, [setting.value, setting.updated_at]);

  const dirty = draft !== setting.value;

  const save = async (value?: string) => {
    const v = value ?? draft;
    await mutation.mutateAsync({ key: setting.key, value: v });
    setSavedFlash(true);
    window.setTimeout(() => setSavedFlash(false), 1500);
  };

  const reset = () => setDraft(setting.value);

  // Display-friendly value for numeric-percent settings.
  const isPercent = setting.unit === "%";

  return (
    <div className="flex flex-col gap-3 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0 flex-1">
        <div className="text-sm font-semibold text-slate-900">{setting.label}</div>
        {setting.description && (
          <div className="mt-0.5 text-[12px] leading-snug text-slate-500">
            {setting.description}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        {setting.value_type === "bool" ? (
          <ToggleSwitch
            checked={draft === "1"}
            onChange={(v) => {
              const next = v ? "1" : "0";
              setDraft(next);
              void save(next);
            }}
            disabled={mutation.isPending}
          />
        ) : setting.value_type === "float" || setting.value_type === "int" ? (
          <NumericControl
            value={draft}
            onChange={setDraft}
            isPercent={isPercent}
            unit={setting.unit ?? undefined}
            min={setting.min_value}
            max={setting.max_value}
          />
        ) : (
          <input
            type="text"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className="w-48 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm"
          />
        )}

        {setting.value_type !== "bool" && (
          <>
            {dirty && (
              <Button
                variant="ghost"
                size="sm"
                onClick={reset}
                disabled={mutation.isPending}
                aria-label="Reset"
              >
                <RotateCcw className="h-3.5 w-3.5" />
              </Button>
            )}
            <Button
              size="sm"
              onClick={() => save()}
              disabled={mutation.isPending || !dirty}
            >
              {mutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              Save
            </Button>
          </>
        )}

        {savedFlash && (
          <span className="flex items-center gap-1 text-xs font-medium text-emerald-600">
            <Check className="h-3.5 w-3.5" />
            Saved
          </span>
        )}
        {mutation.isError && (
          <span className="text-xs text-red-600">
            {(mutation.error as Error).message}
          </span>
        )}
      </div>
    </div>
  );
}

// --- Helpers ---------------------------------------------------------------

function NumericControl({
  value,
  onChange,
  isPercent,
  unit,
  min,
  max,
}: {
  value: string;
  onChange: (v: string) => void;
  isPercent: boolean;
  unit?: string;
  min: number | null;
  max: number | null;
}) {
  // For percent settings, the DB stores 0..1 (e.g., 0.70). We display as
  // 0..100 in the input so admins think in whole percents.
  const displayValue = isPercent
    ? (parseFloat(value) * 100).toFixed(0)
    : value;

  const handleChange = (raw: string) => {
    if (isPercent) {
      const n = parseFloat(raw);
      if (Number.isNaN(n)) {
        onChange("0");
        return;
      }
      onChange((n / 100).toString());
    } else {
      onChange(raw);
    }
  };

  return (
    <div className="relative">
      <input
        type="number"
        value={displayValue}
        onChange={(e) => handleChange(e.target.value)}
        min={isPercent && min != null ? min * 100 : min ?? undefined}
        max={isPercent && max != null ? max * 100 : max ?? undefined}
        step={isPercent ? 1 : "any"}
        className="w-24 rounded-md border border-slate-200 bg-white px-3 py-1.5 pr-8 text-right text-sm tabular-nums text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
      />
      {unit && (
        <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">
          {unit}
        </span>
      )}
    </div>
  );
}

function ToggleSwitch({
  checked,
  onChange,
  disabled,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors",
        checked ? "bg-emerald-500" : "bg-slate-300",
        disabled && "opacity-50",
      )}
    >
      <span
        className={cn(
          "inline-block h-5 w-5 transform rounded-full bg-white shadow ring-1 ring-black/5 transition-transform",
          checked ? "translate-x-5" : "translate-x-0.5",
        )}
      />
    </button>
  );
}
