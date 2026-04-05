import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { TimesheetEntry, TimesheetSummaryRow } from "@/types/timesheet";

export function useTimesheetEntries(params: {
  year?: number;
  month?: string;
  consultantId?: number;
}) {
  return useQuery({
    queryKey: ["timesheets", "entries", params],
    queryFn: async () => {
      const { data } = await api.get<TimesheetEntry[]>("/timesheets/", {
        params: {
          year: params.year,
          month: params.month,
          consultant_id: params.consultantId,
        },
      });
      return data;
    },
  });
}

export function useTimesheetSummary(params: { year?: number; month?: string }) {
  return useQuery({
    queryKey: ["timesheets", "summary", params],
    queryFn: async () => {
      const { data } = await api.get<TimesheetSummaryRow[]>("/timesheets/summary", {
        params,
      });
      return data;
    },
  });
}

export interface TimesheetEntryPayload {
  consultant_id: number;
  entry_date: string;
  project_key?: string | null;
  project_name?: string | null;
  task_description?: string | null;
  work_type: string;
  hours: number;
  notes?: string | null;
}

export function useCreateTimesheetEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TimesheetEntryPayload) => {
      await api.post("/timesheets/", payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["timesheets"] });
      qc.invalidateQueries({ queryKey: ["financials"] });
    },
  });
}

export function useDeleteTimesheetEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (entryId: number) => {
      await api.delete(`/timesheets/${entryId}`);
      return entryId;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["timesheets"] });
      qc.invalidateQueries({ queryKey: ["financials"] });
    },
  });
}
