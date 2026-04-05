import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ProjectDemand } from "@/types/projectDemand";

export function useProjectDemand(projectId: string | undefined) {
  return useQuery({
    queryKey: ["project-demand", projectId],
    enabled: Boolean(projectId),
    queryFn: async () => {
      const { data } = await api.get<ProjectDemand>(`/portfolio/${projectId}/demand`);
      return data;
    },
  });
}
