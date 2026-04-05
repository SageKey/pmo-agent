import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Task } from "@/types/task";

export function useTasks(projectId: string | undefined) {
  return useQuery({
    queryKey: ["tasks", projectId],
    enabled: Boolean(projectId),
    queryFn: async () => {
      const { data } = await api.get<Task[]>(`/tasks/${projectId}`);
      return data;
    },
  });
}
