import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Initiative } from "@/types/initiative";

export const initiativeKeys = {
  all: ["initiatives"] as const,
  list: () => ["initiatives", "list"] as const,
  detail: (id: string) => ["initiatives", "detail", id] as const,
};

export function useInitiatives(status?: string, itOnly?: boolean) {
  return useQuery({
    queryKey: [...initiativeKeys.list(), status, itOnly],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (status) params.status = status;
      if (itOnly !== undefined) params.it_only = String(itOnly);
      const { data } = await api.get<Initiative[]>("/initiatives/", { params });
      return data;
    },
  });
}

export function useInitiative(id: string | undefined) {
  return useQuery({
    queryKey: initiativeKeys.detail(id ?? ""),
    enabled: Boolean(id),
    queryFn: async () => {
      const { data } = await api.get<Initiative>(`/initiatives/${id}`);
      return data;
    },
  });
}

export function useCreateInitiative() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<Initiative> & { id: string; name: string }) => {
      const { data } = await api.post<Initiative>("/initiatives/", payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: initiativeKeys.all }),
  });
}

export function useUpdateInitiative() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...patch }: Partial<Initiative> & { id: string }) => {
      const { data } = await api.patch<Initiative>(`/initiatives/${id}`, patch);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: initiativeKeys.all }),
  });
}

export function useDeleteInitiative() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/initiatives/${id}`);
      return id;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: initiativeKeys.all }),
  });
}
