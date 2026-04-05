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
  Settings,
  Lightbulb,
} from "lucide-react";
import { useHealth } from "@/hooks/useHealth";
import { cn } from "@/lib/cn";

const NAV = [
  { to: "/executive", label: "Executive", icon: LayoutDashboard, publicSafe: true },
  { to: "/portfolio", label: "Portfolio", icon: FolderKanban, publicSafe: true },
  { to: "/capacity", label: "Capacity", icon: Activity, publicSafe: true },
  { to: "/timeline", label: "Timeline", icon: Calendar, publicSafe: true },
  { to: "/financials", label: "Financials", icon: DollarSign, publicSafe: true },
  { to: "/timesheets", label: "Timesheets", icon: Clock, publicSafe: true },
  { to: "/roster", label: "Team Roster", icon: Users, publicSafe: true },
  { to: "/planning", label: "Planning", icon: Lightbulb, publicSafe: true },
  // Hidden when PUBLIC_MODE is on so shared visitors can't burn LLM credit
  { to: "/assistant", label: "AI Assistant", icon: Sparkles, publicSafe: false },
];

export function Sidebar() {
  const { data } = useHealth();
  const publicMode = data?.public_mode === true;
  const showAdmin = data?.show_admin === true;
  const items = NAV.filter((n) => n.publicSafe || !publicMode);

  return (
    <aside className="hidden w-60 shrink-0 border-r border-navy-900/10 bg-navy-950 text-slate-200 md:flex md:flex-col">
      <div className="px-5 py-6">
        <div className="text-lg font-bold text-white">PMO Planner</div>
        <div className="mt-0.5 text-xs text-slate-400">Resource Planning</div>
      </div>
      <nav className="flex-1 space-y-0.5 px-2 pb-6">
        {items.map(({ to, label, icon: Icon }) => (
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
        {showAdmin && (
          <div className="mt-4 border-t border-white/5 pt-4">
            <div className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
              Admin
            </div>
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                cn(
                  "group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-white/10 text-white"
                    : "text-slate-300 hover:bg-white/5 hover:text-white",
                )
              }
            >
              <Settings className="h-4 w-4" />
              Settings
            </NavLink>
          </div>
        )}
      </nav>
      <div className="px-5 pb-6 text-[11px] uppercase tracking-wide text-slate-500">
        v0.1.0 {publicMode ? "· public" : "· local dev"}
      </div>
    </aside>
  );
}
