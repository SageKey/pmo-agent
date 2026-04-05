import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { UtilizationResponse, HeatmapResponse } from "@/types/capacity";

export const capacityKeys = {
  utilization: ["capacity", "utilization"] as const,
  heatmap: (weeks: number) => ["capacity", "heatmap", weeks] as const,
};

export function useUtilization() {
  return useQuery({
    queryKey: capacityKeys.utilization,
    queryFn: async () => {
      const { data } = await api.get<UtilizationResponse>("/capacity/utilization");
      return data;
    },
  });
}

export function useHeatmap(weeks = 26) {
  return useQuery({
    queryKey: capacityKeys.heatmap(weeks),
    queryFn: async () => {
      const { data } = await api.get<HeatmapResponse>("/capacity/heatmap", {
        params: { weeks },
      });
      return data;
    },
  });
}
