import { Badge } from "@/components/ui/badge";

const MAP: Record<string, { tone: "green" | "yellow" | "red" | "slate" | "navy"; label: string }> = {
  "ON TRACK": { tone: "green", label: "On track" },
  "AT RISK": { tone: "yellow", label: "At risk" },
  "NEEDS HELP": { tone: "red", label: "Needs help" },
  "NEEDS FUNCTIONAL SPEC": { tone: "navy", label: "Needs spec" },
  "NEEDS TECHNICAL SPEC": { tone: "navy", label: "Needs spec" },
  "NOT STARTED": { tone: "slate", label: "Not started" },
  COMPLETE: { tone: "green", label: "Complete" },
  POSTPONED: { tone: "slate", label: "Postponed" },
};

export function HealthBadge({ health }: { health: string | null }) {
  if (!health) return <span className="text-slate-400">—</span>;
  const key = Object.keys(MAP).find((k) => health.toUpperCase().includes(k));
  const info = key ? MAP[key] : { tone: "slate" as const, label: health };
  return <Badge tone={info.tone}>{info.label}</Badge>;
}
