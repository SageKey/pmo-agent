export interface Milestone {
  id: number;
  project_id: string;
  title: string;
  milestone_type: string | null;
  due_date: string | null;
  completed_date: string | null;
  status: string | null;
  owner: string | null;
  jira_epic_key: string | null;
  progress_pct: number;
  sort_order: number | null;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}
