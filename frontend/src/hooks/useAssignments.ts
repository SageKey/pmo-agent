import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Assignment } from "@/types/assignment";

const assignmentKeys = {
  all: ["assignments"] as const,
  forProject: (id: string | undefined) => ["assignments", "project", id] as const,
  forPerson: (name: string | undefined) => ["assignments", "person", name] as const,
};

export function useProjectAssignments(projectId: string | undefined) {
  return useQuery({
    queryKey: assignmentKeys.forProject(projectId),
    enabled: Boolean(projectId),
    queryFn: async () => {
      const { data } = await api.get<Assignment[]>("/assignments/", {
        params: { project_id: projectId },
      });
      return data;
    },
  });
}

export interface AssignmentPayload {
  project_id: string;
  person_name: string;
  role_key: string;
  allocation_pct: number;
}

export function useUpsertAssignment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: AssignmentPayload) => {
      const { data } = await api.post<Assignment>("/assignments/", payload);
      return data;
    },
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: assignmentKeys.all });
      qc.invalidateQueries({
        queryKey: assignmentKeys.forProject(variables.project_id),
      });
      // Roster demand depends on assignments — invalidate so Team Roster
      // + Executive summary update with the new person-level numbers.
      qc.invalidateQueries({ queryKey: ["roster"] });
      qc.invalidateQueries({ queryKey: ["capacity"] });
    },
  });
}

export function useDeleteAssignment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      project_id: string;
      person_name: string;
      role_key: string;
    }) => {
      await api.delete("/assignments/", { params: payload });
      return payload;
    },
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: assignmentKeys.all });
      qc.invalidateQueries({
        queryKey: assignmentKeys.forProject(variables.project_id),
      });
      qc.invalidateQueries({ queryKey: ["roster"] });
      qc.invalidateQueries({ queryKey: ["capacity"] });
    },
  });
}
