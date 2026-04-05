export interface PhaseHours {
  phase: string;
  weekly_hours: number;
}

export interface ProjectRoleDemand {
  role_key: string;
  role_alloc_pct: number;
  weekly_hours: number;
  phase_breakdown: PhaseHours[];
}

export interface ProjectDemand {
  project_id: string;
  duration_weeks: number;
  total_est_hours: number;
  roles: ProjectRoleDemand[];
}
