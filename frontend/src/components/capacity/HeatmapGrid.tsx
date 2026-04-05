import type { HeatmapResponse } from "@/types/capacity";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Brett's locked-in color rule: green / yellow / red only, 0% = empty.
function cellStyle(util: number): { bg: string; text: string } {
  if (util <= 0) return { bg: "bg-slate-50", text: "text-slate-300" };
  if (util < 0.8) return { bg: "bg-emerald-100", text: "text-emerald-800" };
  if (util < 1.0) return { bg: "bg-amber-200", text: "text-amber-900" };
  if (util < 1.25) return { bg: "bg-red-300", text: "text-red-900" };
  return { bg: "bg-red-500", text: "text-white" };
}

const ROLE_LABEL: Record<string, string> = {
  pm: "PM",
  ba: "BA",
  functional: "Functional",
  technical: "Technical",
  developer: "Developer",
  infrastructure: "Infra",
  dba: "DBA",
  wms: "WMS",
};

export function HeatmapGrid({ data }: { data: HeatmapResponse }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Utilization heatmap · next {data.weeks.length} weeks</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr>
                <th className="sticky left-0 z-10 bg-white py-2 pr-3 text-left font-semibold text-slate-500">
                  Role
                </th>
                {data.weeks.map((w) => (
                  <th
                    key={w}
                    className="min-w-[52px] px-1 py-2 text-center font-medium text-slate-500"
                  >
                    {w}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row) => (
                <tr key={row.role_key}>
                  <td className="sticky left-0 z-10 bg-white py-1 pr-3 text-left font-semibold text-slate-700">
                    {ROLE_LABEL[row.role_key] ?? row.role_key}
                  </td>
                  {row.cells.map((c, i) => {
                    const { bg, text } = cellStyle(c);
                    return (
                      <td key={i} className="p-0.5">
                        <div
                          className={`flex h-8 items-center justify-center rounded ${bg} ${text} tabular-nums`}
                          title={`${row.role_key} · ${data.weeks[i]} · ${(c * 100).toFixed(0)}%`}
                        >
                          {c > 0 ? `${Math.round(c * 100)}` : ""}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-4 flex items-center gap-4 text-xs text-slate-500">
          <LegendSwatch className="bg-slate-50 ring-1 ring-slate-200" label="0%" />
          <LegendSwatch className="bg-emerald-100" label="< 80%" />
          <LegendSwatch className="bg-amber-200" label="80 – 100%" />
          <LegendSwatch className="bg-red-300" label="100 – 125%" />
          <LegendSwatch className="bg-red-500" label="> 125%" />
        </div>
      </CardContent>
    </Card>
  );
}

function LegendSwatch({ className, label }: { className: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className={`h-3 w-5 rounded ${className}`} />
      <span>{label}</span>
    </div>
  );
}
