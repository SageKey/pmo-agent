import * as React from "react";
import { cn } from "@/lib/cn";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: "default" | "green" | "yellow" | "red" | "slate" | "navy";
}

const TONE: Record<NonNullable<BadgeProps["tone"]>, string> = {
  default: "bg-slate-100 text-slate-700",
  green: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200",
  yellow: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200",
  red: "bg-red-50 text-red-700 ring-1 ring-inset ring-red-200",
  slate: "bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-200",
  navy: "bg-navy-50 text-navy-800 ring-1 ring-inset ring-navy-200",
};

export function Badge({ className, tone = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        TONE[tone],
        className,
      )}
      {...props}
    />
  );
}
