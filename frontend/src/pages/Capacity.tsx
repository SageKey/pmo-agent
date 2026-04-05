import { TopBar } from "@/components/layout/TopBar";
import { UtilizationBars } from "@/components/capacity/UtilizationBars";
import { HeatmapGrid } from "@/components/capacity/HeatmapGrid";
import { useHeatmap, useUtilization } from "@/hooks/useCapacity";

export function Capacity() {
  const util = useUtilization();
  const heat = useHeatmap(26);

  return (
    <>
      <TopBar
        title="Capacity"
        subtitle="Role-level utilization and 26-week forward view."
      />
      <div className="space-y-6 p-8">
        {util.isLoading && <LoadingCard text="Computing utilization…" />}
        {util.isError && <ErrorCard err={util.error as Error} />}
        {util.data && <UtilizationBars roles={util.data.roles} />}

        {heat.isLoading && <LoadingCard text="Building heatmap…" />}
        {heat.isError && <ErrorCard err={heat.error as Error} />}
        {heat.data && <HeatmapGrid data={heat.data} />}
      </div>
    </>
  );
}

function LoadingCard({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}

function ErrorCard({ err }: { err: Error }) {
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-800">
      {err.message}
    </div>
  );
}
