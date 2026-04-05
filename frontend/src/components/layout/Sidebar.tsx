import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FolderKanban,
  Activity,
  Calendar,
  DollarSign,
  Clock,
  Users,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/cn";

const NAV = [
  { to: "/executive", label: "Executive", icon: LayoutDashboard },
  { to: "/portfolio", label: "Portfolio", icon: FolderKanban },
  { to: "/capacity", label: "Capacity", icon: Activity },
  { to: "/timeline", label: "Timeline", icon: Calendar },
  { to: "/financials", label: "Financials", icon: DollarSign },
  { to: "/timesheets", label: "Timesheets", icon: Clock },
  { to: "/roster", label: "Team Roster", icon: Users },
  { to: "/assistant", label: "AI Assistant", icon: Sparkles },
];

export function Sidebar() {
  return (
    <aside className="hidden w-60 shrink-0 border-r border-navy-900/10 bg-navy-950 text-slate-200 md:flex md:flex-col">
      <div className="px-5 py-6">
        <div className="text-lg font-bold text-white">ETE IT PMO</div>
        <div className="mt-0.5 text-xs text-slate-400">Resource Planning</div>
      </div>
      <nav className="flex-1 space-y-0.5 px-2 pb-6">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-white/10 text-white"
                  : "text-slate-300 hover:bg-white/5 hover:text-white",
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-5 pb-6 text-[11px] uppercase tracking-wide text-slate-500">
        v0.1.0 · local dev
      </div>
    </aside>
  );
}
