export interface Task {
  id: number;
  project_id: string;
  milestone_id: number | null;
  parent_task_id: number | null;
  title: string;
  notes: string | null; // Rich HTML (renamed from description in v7)
  assignee: string | null;
  role_key: string | null;
  start_date: string | null;
  end_date: string | null;
  est_hours: number;
  actual_hours: number;
  status: string | null;
  progress_pct: number;
  priority: string | null;
  jira_key: string | null;
  sort_order: number | null;
  created_at: string | null;
  updated_at: string | null;
  updated_by: string | null;
}
