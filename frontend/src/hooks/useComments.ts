import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Comment } from "@/types/comment";

const commentKeys = {
  list: (projectId: string | undefined, limit: number) =>
    ["comments", projectId, limit] as const,
  allFor: (projectId: string | undefined) => ["comments", projectId] as const,
};

export function useComments(projectId: string | undefined, limit = 50) {
  return useQuery({
    queryKey: commentKeys.list(projectId, limit),
    enabled: Boolean(projectId),
    queryFn: async () => {
      const { data } = await api.get<Comment[]>(`/comments/${projectId}`, {
        params: { limit },
      });
      return data;
    },
  });
}

export function useAddComment(projectId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { author: string; body: string }) => {
      const { data } = await api.post<Comment>(`/comments/${projectId}`, payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: commentKeys.allFor(projectId) });
    },
  });
}

export function useDeleteComment(projectId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (commentId: number) => {
      await api.delete(`/comments/id/${commentId}`);
      return commentId;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: commentKeys.allFor(projectId) });
    },
  });
}
