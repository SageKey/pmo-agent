import { useHealth } from "@/hooks/useHealth";
import { shortDate } from "@/lib/format";

export function TopBar({ title, subtitle }: { title: string; subtitle?: string }) {
  const { data } = useHealth();

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-8 py-5">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-6 text-xs text-slate-500">
        {data && (
          <>
            <div>
              <span className="font-semibold text-slate-700">{data.active_project_count}</span>{" "}
              active · {data.project_count} total
            </div>
            <div>
              <span className="font-semibold text-slate-700">{data.roster_count}</span> team
              members
            </div>
            <div>Data as of {shortDate(data.db_mtime)}</div>
          </>
        )}
      </div>
    </header>
  );
}
