export interface RoleDemand {
  project_id: string;
  project_name: string;
  role_key: string;
  role_alloc_pct: number;
  weekly_hours: number;
}

// GREY is the "unstaffed" case: role has demand > 0 but supply = 0 (no
// roster members, or all excluded via include_in_capacity). Distinct from
// RED because it's a staffing gap, not an over-allocation.
export type RoleStatus = "BLUE" | "GREEN" | "YELLOW" | "RED" | "GREY";

export interface RoleUtilization {
  role_key: string;
  supply_hrs_week: number;
  demand_hrs_week: number;
  utilization_pct: number;
  status: RoleStatus;
  demand_breakdown: RoleDemand[];
}

export interface UtilizationResponse {
  roles: Record<string, RoleUtilization>;
}

export interface HeatmapRow {
  role_key: string;
  supply_hrs_week: number;
  cells: number[];
}

export interface HeatmapResponse {
  weeks: string[];
  rows: HeatmapRow[];
}
