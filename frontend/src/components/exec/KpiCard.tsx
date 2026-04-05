import * as React from "react";
import { motion } from "framer-motion";
import { Check, TrendingUp, AlertTriangle, Users } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/cn";

type Tone = "neutral" | "success" | "warning" | "danger";

const TONE_STYLES: Record<
  Tone,
  { ring: string; icon: string; iconBg: string; bar: string; valueText: string }
> = {
  neutral: {
    ring: "ring-slate-200",
    icon: "text-slate-600",
    iconBg: "bg-slate-100",
    bar: "bg-slate-400",
    valueText: "text-slate-900",
  },
  success: {
    ring: "ring-emerald-200",
    icon: "text-emerald-700",
    iconBg: "bg-emerald-100",
    bar: "bg-emerald-500",
    valueText: "text-slate-900",
  },
  warning: {
    ring: "ring-amber-200",
    icon: "text-amber-700",
    iconBg: "bg-amber-100",
    bar: "bg-amber-500",
    valueText: "text-slate-900",
  },
  danger: {
    ring: "ring-red-200",
    icon: "text-red-700",
    iconBg: "bg-red-100",
    bar: "bg-red-500",
    valueText: "text-slate-900",
  },
};

export interface KpiCardProps {
  label: string;
  value: React.ReactNode;
  /** Small line under the value (e.g. "of 38 total · 39% in-flight"). */
  subvalue?: React.ReactNode;
  icon?: React.ReactNode;
  tone?: Tone;
  /** Stagger delay for mount animation. */
  delay?: number;
}

export function KpiCard({
  label,
  value,
  subvalue,
  icon,
  tone = "neutral",
  delay = 0,
}: KpiCardProps) {
  const t = TONE_STYLES[tone];
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay, ease: "easeOut" }}
      className="h-full"
    >
      <Card className={cn("flex h-full flex-col ring-1 ring-inset", t.ring)}>
        <div className="flex h-full flex-col p-5">
          <div className="flex items-start justify-between">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              {label}
            </div>
            {icon && (
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-lg",
                  t.iconBg,
                  t.icon,
                )}
              >
                {icon}
              </div>
            )}
          </div>
          <div className={cn("mt-3 text-4xl font-bold tabular-nums", t.valueText)}>
            <CountUp value={value} />
          </div>
          <div className="mt-auto pt-2 text-xs text-slate-500 min-h-[2.25rem]">
            {subvalue ?? ""}
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

/** Only count-ups whole numbers; passes through strings and ReactNodes as-is. */
function CountUp({ value }: { value: React.ReactNode }) {
  const [display, setDisplay] = React.useState<React.ReactNode>(value);

  React.useEffect(() => {
    if (typeof value !== "number" && typeof value !== "string") {
      setDisplay(value);
      return;
    }
    // Extract leading integer if the value is a string like "19%"
    const raw = typeof value === "number" ? value : value;
    const match = typeof raw === "string" ? raw.match(/^(-?\d+)(.*)$/) : null;
    const target = typeof value === "number" ? value : match ? parseInt(match[1], 10) : null;
    const suffix = typeof value === "string" && match ? match[2] : "";
    if (target == null || Number.isNaN(target)) {
      setDisplay(value);
      return;
    }
    const duration = 600;
    const start = performance.now();
    let raf = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      const current = Math.round(target * eased);
      setDisplay(`${current}${suffix}`);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value]);

  return <>{display}</>;
}

// Re-export icons so the page can reference them without importing lucide directly
export const KpiIcons = { Check, TrendingUp, AlertTriangle, Users };
