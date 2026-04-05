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
  | { type: "add_person"; person: AddPersonPayload };

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
