export interface InitiativeProjectSummary {
  id: string;
  name: string;
  health: string | null;
  pct_complete: number;
  priority: string | null;
  planned_it_start: string | null;
}

export interface Initiative {
  id: string;
  name: string;
  description: string | null;
  sponsor: string | null;
  status: "Active" | "Complete" | "On Hold";
  it_involvement: boolean;
  priority: string | null;
  target_start: string | null;
  target_end: string | null;
  sort_order: number;
  created_at: string | null;
  updated_at: string | null;
  project_count: number;
  projects: InitiativeProjectSummary[];
}
