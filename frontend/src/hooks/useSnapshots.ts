import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface Snapshot {
  id: number;
  taken_at: string;
  project_count: number | null;
  active_count: number | null;
  notes: string | null;
}

export interface ChangeEntry {
  project_id: string;
  project_name: string;
  [key: string]: unknown;
}

export interface ChangesResponse {
  has_previous: boolean;
  message?: string;
  previous_snapshot?: {
    id: number;
    taken_at: string;
    project_count: number;
    active_count: number;
  };
  new_projects: ChangeEntry[];
  removed_projects: ChangeEntry[];
  status_changes: ChangeEntry[];
  progress_changes: ChangeEntry[];
  date_changes: ChangeEntry[];
  priority_changes: ChangeEntry[];
  hours_changes: ChangeEntry[];
}

export function useLatestSnapshot() {
  return useQuery({
    queryKey: ["snapshots", "latest"],
    queryFn: async () => {
      const { data } = await api.get<Snapshot | null>("/snapshots/latest");
      return data;
    },
  });
}

export function useDetectChanges() {
  return useQuery({
    queryKey: ["snapshots", "detect-changes"],
    queryFn: async () => {
      const { data } = await api.get<ChangesResponse>(
        "/snapshots/detect-changes",
      );
      return data;
    },
    staleTime: 30_000,
  });
}

export function useCreateSnapshot() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (notes: string = "") => {
      const { data } = await api.post<Snapshot>("/snapshots/", { notes });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["snapshots"] });
    },
  });
}
