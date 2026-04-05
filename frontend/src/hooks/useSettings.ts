import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { AppSetting } from "@/types/settings";

const settingsKeys = {
  all: ["settings"] as const,
  category: (c: string) => ["settings", "category", c] as const,
};

export function useSettings(category?: string) {
  return useQuery({
    queryKey: category ? settingsKeys.category(category) : settingsKeys.all,
    queryFn: async () => {
      const params = category ? { category } : {};
      const { data } = await api.get<AppSetting[]>("/settings/", { params });
      return data;
    },
    staleTime: 30_000,
  });
}

export function useUpdateSetting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ key, value }: { key: string; value: string }) => {
      const { data } = await api.put<AppSetting>(`/settings/${encodeURIComponent(key)}`, {
        value,
      });
      return data;
    },
    onSuccess: () => {
      // Changing a threshold affects downstream capacity computations, so
      // blow away related caches.
      qc.invalidateQueries({ queryKey: settingsKeys.all });
      qc.invalidateQueries({ queryKey: ["capacity"] });
      qc.invalidateQueries({ queryKey: ["roster"] });
    },
  });
}
