import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Project } from "@/types/project";

export const portfolioKeys = {
  all: ["portfolio"] as const,
  list: (activeOnly: boolean) => ["portfolio", "list", activeOnly] as const,
  detail: (id: string) => ["portfolio", "detail", id] as const,
};

export function usePortfolio(activeOnly = false) {
  return useQuery({
    queryKey: portfolioKeys.list(activeOnly),
    queryFn: async () => {
      const { data } = await api.get<Project[]>("/portfolio/", {
        params: { active_only: activeOnly },
      });
      return data;
    },
  });
}

export function useProject(id: string | undefined) {
  return useQuery({
    queryKey: portfolioKeys.detail(id ?? ""),
    enabled: Boolean(id),
    queryFn: async () => {
      const { data } = await api.get<Project>(`/portfolio/${id}`);
      return data;
    },
  });
}
