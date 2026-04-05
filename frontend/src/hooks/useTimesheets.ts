import { useQuery } from "@tanstack/react-query";
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
