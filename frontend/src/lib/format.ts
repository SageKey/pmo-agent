export function pct(n: number, digits = 0): string {
  if (Number.isNaN(n) || n == null) return "—";
  return `${(n * 100).toFixed(digits)}%`;
}

export function hours(n: number): string {
  if (n == null || Number.isNaN(n)) return "—";
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k hrs`;
  return `${Math.round(n)} hrs`;
}

export function currency(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

export function shortDate(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(d.getUTCDate()).padStart(2, "0");
  const yyyy = d.getUTCFullYear();
  return `${mm}-${dd}-${yyyy}`;
}

/** Month + year only, e.g. "04-2026". */
export function shortMonthYear(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
  return `${mm}-${d.getUTCFullYear()}`;
}

/** "Alex Young" → "AY", "Emily Fridley" → "EF", null → "—" */
export function initials(name?: string | null): string {
  if (!name) return "—";
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "—";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/** Deterministic hash → index into a small palette, so the same name always
 *  gets the same avatar color. Pure Tailwind class strings. */
const AVATAR_COLORS = [
  "bg-sky-100 text-sky-700",
  "bg-violet-100 text-violet-700",
  "bg-emerald-100 text-emerald-700",
  "bg-amber-100 text-amber-700",
  "bg-rose-100 text-rose-700",
  "bg-teal-100 text-teal-700",
  "bg-indigo-100 text-indigo-700",
  "bg-fuchsia-100 text-fuchsia-700",
];
export function avatarTone(name?: string | null): string {
  if (!name) return AVATAR_COLORS[0];
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return AVATAR_COLORS[h % AVATAR_COLORS.length];
}

/** Time-ago label for past timestamps: "just now", "5m ago", "2h ago",
 * "3d ago", "04-05" (date) if older than 14 days. */
export function timeAgo(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const diffMs = Date.now() - d.getTime();
  const diffMin = Math.round(diffMs / 60_000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.round(diffHr / 24);
  if (diffDay < 14) return `${diffDay}d ago`;
  // Older — show MM-DD
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${mm}-${dd}`;
}

/** Relative date label: "in 6 wks", "in 3 days", "overdue 2 wks", "today". */
export function relativeDate(iso?: string | null): { label: string; tone: "past" | "soon" | "future" | "none" } {
  if (!iso) return { label: "—", tone: "none" };
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return { label: "—", tone: "none" };
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const target = new Date(d);
  target.setHours(0, 0, 0, 0);
  const diffDays = Math.round((target.getTime() - now.getTime()) / 86_400_000);
  if (diffDays === 0) return { label: "today", tone: "soon" };
  if (diffDays > 0) {
    const tone = diffDays <= 14 ? "soon" : "future";
    if (diffDays < 14) return { label: `in ${diffDays}d`, tone };
    if (diffDays < 60) return { label: `in ${Math.round(diffDays / 7)}w`, tone };
    return { label: `in ${Math.round(diffDays / 30)}mo`, tone };
  }
  const past = Math.abs(diffDays);
  if (past < 14) return { label: `${past}d late`, tone: "past" };
  if (past < 60) return { label: `${Math.round(past / 7)}w late`, tone: "past" };
  return { label: `${Math.round(past / 30)}mo late`, tone: "past" };
}
