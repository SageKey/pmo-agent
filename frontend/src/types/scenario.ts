import type { RoleStatus } from "./capacity";

// ---------------------------------------------------------------------------
// Modification payloads — discriminated union on `type`
// ---------------------------------------------------------------------------

export interface AddProjectPayload {
  id?: string;
  name: string;
  type?: string | null;
  portfolio?: string | null;
  sponsor?: string | null;
  priority?: string;
  start_date: string; // ISO YYYY-MM-DD
  end_date: string;
  est_hours: number;
  role_allocations: Record<string, number>;
}

export interface AddPersonPayload {
  name: string;
  role_key: string;
  role?: string | null;
  team?: string | null;
  vendor?: string | null;
  classification?: string | null;
  rate_per_hour?: number;
  weekly_hrs_available: number;
  support_reserve_pct?: number;
}

export type ScenarioModification =
  | { type: "add_project"; project: AddProjectPayload }
  | { type: "cancel_project"; project_id: string }
  | { type: "exclude_person"; person_name: string }
  | { type: "add_person"; person: AddPersonPayload }
  | { type: "shift_project"; project_id: string; new_start_date?: string; new_end_date?: string }
  | { type: "change_allocation"; project_id: string; role_key: string; allocation: number }
  | { type: "resize_project"; project_id: string; est_hours: number };

// ---------------------------------------------------------------------------
// Request / response
// ---------------------------------------------------------------------------

export interface ScenarioEvaluateRequest {
  name?: string;
  modifications: ScenarioModification[];
}

export interface RoleUtilSnapshot {
  role_key: string;
  supply_hrs_week: number;
  demand_hrs_week: number;
  utilization_pct: number;
  status: RoleStatus;
}

export interface UtilizationSide {
  roles: Record<string, RoleUtilSnapshot>;
}

export interface ScenarioDelta {
  role_key: string;
  baseline_pct: number;
  scenario_pct: number;
  delta_pct: number;
  baseline_status: RoleStatus;
  scenario_status: RoleStatus;
  status_changed: boolean;
}

export interface ScenarioSummary {
  headline: string;
  became_over: string[];
  became_stretched: string[];
  became_unstaffed: string[];
  became_better: string[];
}

export interface ScenarioEvaluateResponse {
  baseline: UtilizationSide;
  scenario: UtilizationSide;
  deltas: ScenarioDelta[];
  summary: ScenarioSummary;
}

// ---------------------------------------------------------------------------
// Auto-scheduler — project placement
// ---------------------------------------------------------------------------

export interface SchedulePortfolioRequest {
  max_util_pct?: number;
  horizon_weeks?: number;
  exclude_ids?: string[];
  modifications?: ScenarioModification[];
}

export interface ScheduledProject {
  project_id: string;
  project_name: string;
  priority: string;
  est_hours: number;
  health: string;
  suggested_start: string | null;
  suggested_end: string | null;
  duration_weeks: number;
  wait_weeks: number | null;
  bottleneck_role: string | null;
  can_start_now: boolean;
}

export interface InFlightProject {
  project_id: string;
  project_name: string;
  priority: string;
  est_hours: number;
  health: string;
  pct_complete: number;
  start_date: string | null;
  end_date: string | null;
}

export interface SchedulePortfolioResponse {
  max_util_pct: number;
  horizon_weeks: number;
  in_flight: InFlightProject[];
  projects: ScheduledProject[];
  can_start_now_count: number;
  waiting_count: number;
  infeasible_count: number;
  bottleneck_roles: Record<string, number>;
}
