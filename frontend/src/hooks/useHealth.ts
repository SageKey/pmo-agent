import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface HealthResponse {
  status: string;
  db_path: string;
  db_mtime: string | null;
  project_count: number;
  active_project_count: number;
  roster_count: number;
  version: string;
}

export function useHealth() {
  return useQuery({
    queryKey: ["meta", "health"],
    queryFn: async () => {
      const { data } = await api.get<HealthResponse>("/meta/health");
      return data;
    },
    staleTime: 60_000,
  });
}
