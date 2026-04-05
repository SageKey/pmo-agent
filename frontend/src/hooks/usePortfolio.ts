import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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

/** Partial update payload matching backend ProjectUpdate schema. */
export type ProjectPatch = Partial<{
  name: string;
  type: string | null;
  portfolio: string | null;
  sponsor: string | null;
  health: string | null;
  pct_complete: number;
  priority: string | null;
  start_date: string | null;
  end_date: string | null;
  actual_end: string | null;
  pm: string | null;
  ba: string | null;
  functional_lead: string | null;
  technical_lead: string | null;
  developer_lead: string | null;
  tshirt_size: string | null;
  est_hours: number;
  budget: number;
  actual_cost: number;
  forecast_cost: number;
  notes: string | null;
  role_allocations: Record<string, number>;
}>;

export function useUpdateProject(projectId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (patch: ProjectPatch) => {
      const { data } = await api.patch<Project>(`/portfolio/${projectId}`, patch);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: portfolioKeys.all });
      if (projectId) {
        qc.invalidateQueries({ queryKey: portfolioKeys.detail(projectId) });
      }
    },
  });
}

export interface ProjectCreatePayload {
  id: string;
  name: string;
  priority?: string | null;
  health?: string | null;
  pm?: string | null;
  portfolio?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  est_hours?: number;
  pct_complete?: number;
  budget?: number;
  notes?: string | null;
  role_allocations?: Record<string, number>;
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ProjectCreatePayload) => {
      const { data } = await api.post<Project>("/portfolio/", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: portfolioKeys.all });
    },
  });
}

export function useDeleteProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (projectId: string) => {
      await api.delete(`/portfolio/${projectId}`);
      return projectId;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: portfolioKeys.all });
      qc.invalidateQueries({ queryKey: ["capacity"] });
      qc.invalidateQueries({ queryKey: ["assignments"] });
    },
  });
}
