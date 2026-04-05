import { cn } from "@/lib/cn";

const TONE: Record<string, string> = {
  Highest: "bg-red-50 text-red-700 ring-red-200",
  High: "bg-amber-50 text-amber-700 ring-amber-200",
  Medium: "bg-sky-50 text-sky-700 ring-sky-200",
  Low: "bg-slate-100 text-slate-600 ring-slate-200",
};

export function PriorityPill({ priority }: { priority: string | null }) {
  if (!priority) return <span className="text-slate-400">—</span>;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset",
        TONE[priority] ?? "bg-slate-100 text-slate-700 ring-slate-200",
      )}
    >
      {priority}
    </span>
  );
}
