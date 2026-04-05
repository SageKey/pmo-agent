import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Milestone } from "@/types/milestone";

const milestoneKeys = {
  list: (projectId: string | undefined) => ["milestones", projectId] as const,
};

export interface MilestoneCreatePayload {
  title: string;
  milestone_type?: string;
  due_date?: string | null;
  status?: string;
  owner?: string | null;
  jira_epic_key?: string | null;
  progress_pct?: number;
  sort_order?: number;
  notes?: string | null;
}

export interface MilestoneUpdatePayload extends MilestoneCreatePayload {
  project_id: string;
}

export function useMilestones(projectId: string | undefined) {
  return useQuery({
    queryKey: milestoneKeys.list(projectId),
    enabled: Boolean(projectId),
    queryFn: async () => {
      const { data } = await api.get<Milestone[]>(`/milestones/${projectId}`);
      return data;
    },
  });
}

export function useAddMilestone(projectId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: MilestoneCreatePayload) => {
      const { data } = await api.post<Milestone>(
        `/milestones/${projectId}`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: milestoneKeys.list(projectId) });
    },
  });
}

export function useUpdateMilestone(projectId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      payload,
    }: {
      id: number;
      payload: MilestoneUpdatePayload;
    }) => {
      const { data } = await api.put<Milestone>(
        `/milestones/id/${id}`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: milestoneKeys.list(projectId) });
    },
  });
}

export function useCompleteMilestone(projectId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (milestoneId: number) => {
      await api.post(`/milestones/id/${milestoneId}/complete`);
      return milestoneId;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: milestoneKeys.list(projectId) });
    },
  });
}

export function useDeleteMilestone(projectId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (milestoneId: number) => {
      await api.delete(`/milestones/id/${milestoneId}`);
      return milestoneId;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: milestoneKeys.list(projectId) });
    },
  });
}
