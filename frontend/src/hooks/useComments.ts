import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Comment } from "@/types/comment";

export function useComments(projectId: string | undefined, limit = 50) {
  return useQuery({
    queryKey: ["comments", projectId, limit],
    enabled: Boolean(projectId),
    queryFn: async () => {
      const { data } = await api.get<Comment[]>(`/comments/${projectId}`, {
        params: { limit },
      });
      return data;
    },
  });
}
