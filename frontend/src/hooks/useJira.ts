import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface JiraSyncChange {
  project_id: string;
  project_name: string;
  old_pct: number;
  new_pct: number;
  old_health: string | null;
  new_health: string | null;
  pct_changed: boolean;
  health_changed: boolean;
}

export interface JiraSyncResponse {
  timestamp: string;
  total_projects: number;
  matched: number;
  updated: number;
  skipped: number;
  errors: number;
  changes: JiraSyncChange[];
  error: string | null;
}

export function useJiraSync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<JiraSyncResponse>("/jira/sync");
      return data;
    },
    onSuccess: (data) => {
      if (data.updated > 0) {
        qc.invalidateQueries({ queryKey: ["portfolio"] });
        qc.invalidateQueries({ queryKey: ["capacity"] });
      }
    },
  });
}
