export interface TimesheetEntry {
  id: number;
  consultant_id: number;
  consultant_name: string | null;
  billing_type: string | null;
  hourly_rate: number | null;
  entry_date: string;
  project_key: string | null;
  project_name: string | null;
  task_description: string | null;
  work_type: string | null;
  hours: number;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface TimesheetSummaryRow {
  consultant_id: number;
  name: string;
  billing_type: string | null;
  hourly_rate: number | null;
  project_hours: number;
  support_hours: number;
  total_hours: number;
  tm_cost: number;
}
