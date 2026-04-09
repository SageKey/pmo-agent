import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Task } from "@/types/task";

const taskKeys = {
  all: ["tasks"] as const,
  list: (projectId: string) => ["tasks", projectId] as const,
};

export function useTasks(projectId: string | undefined) {
  return useQuery({
    queryKey: taskKeys.list(projectId ?? ""),
    enabled: Boolean(projectId),
    queryFn: async () => {
      const { data } = await api.get<Task[]>(`/tasks/${projectId}`);
      return data;
    },
  });
}

export interface TaskCreatePayload {
  title: string;
  milestone_id?: number | null;
  parent_task_id?: number | null;
  description?: string | null;
  assignee?: string | null;
  role_key?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  est_hours?: number;
  status?: string;
  progress_pct?: number;
  priority?: string;
  sort_order?: number;
}

export interface TaskUpdatePayload extends Partial<TaskCreatePayload> {
  project_id: string; // required for the backend audit log
}

export function useCreateTask(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TaskCreatePayload) => {
      const { data } = await api.post<Task>(`/tasks/${projectId}`, payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: taskKeys.list(projectId) });
    },
  });
}

export function useUpdateTask(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...patch }: TaskUpdatePayload & { id: number }) => {
      const { data } = await api.patch<Task>(`/tasks/id/${id}`, patch);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: taskKeys.list(projectId) });
    },
  });
}

export function useCompleteTask(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (taskId: number) => {
      await api.post(`/tasks/id/${taskId}/complete`);
      return taskId;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: taskKeys.list(projectId) });
    },
  });
}

export function useDeleteTask(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (taskId: number) => {
      await api.delete(`/tasks/id/${taskId}`);
      return taskId;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: taskKeys.list(projectId) });
    },
  });
}
