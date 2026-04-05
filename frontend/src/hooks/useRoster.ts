import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PersonDemand, TeamMember } from "@/types/roster";

const rosterKeys = {
  all: ["roster"] as const,
  list: ["roster", "list"] as const,
  demand: ["roster", "demand"] as const,
};

export function useRoster() {
  return useQuery({
    queryKey: rosterKeys.list,
    queryFn: async () => {
      const { data } = await api.get<TeamMember[]>("/roster/");
      return data;
    },
  });
}

export function usePersonDemand() {
  return useQuery({
    queryKey: rosterKeys.demand,
    queryFn: async () => {
      const { data } = await api.get<PersonDemand[]>("/roster/demand");
      return data;
    },
  });
}

export interface RosterMemberPayload {
  name: string;
  role: string;
  role_key: string;
  team?: string | null;
  vendor?: string | null;
  classification?: string | null;
  rate_per_hour: number;
  weekly_hrs_available: number;
  support_reserve_pct: number;
  include_in_capacity: boolean;
}

export function useCreateMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: RosterMemberPayload) => {
      const { data } = await api.post<TeamMember>("/roster/", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: rosterKeys.all });
      qc.invalidateQueries({ queryKey: ["capacity"] });
    },
  });
}

export function useUpdateMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      originalName,
      payload,
    }: {
      originalName: string;
      payload: RosterMemberPayload;
    }) => {
      const { data } = await api.put<TeamMember>(
        `/roster/${encodeURIComponent(originalName)}`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: rosterKeys.all });
      qc.invalidateQueries({ queryKey: ["capacity"] });
    },
  });
}

export function useDeleteMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (name: string) => {
      await api.delete(`/roster/${encodeURIComponent(name)}`);
      return name;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: rosterKeys.all });
      qc.invalidateQueries({ queryKey: ["capacity"] });
      qc.invalidateQueries({ queryKey: ["assignments"] });
    },
  });
}
