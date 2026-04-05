import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Milestone } from "@/types/milestone";

export function useMilestones(projectId: string | undefined) {
  return useQuery({
    queryKey: ["milestones", projectId],
    enabled: Boolean(projectId),
    queryFn: async () => {
      const { data } = await api.get<Milestone[]>(`/milestones/${projectId}`);
      return data;
    },
  });
}
