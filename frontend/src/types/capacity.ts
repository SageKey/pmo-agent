export interface RoleDemand {
  project_id: string;
  project_name: string;
  role_key: string;
  role_alloc_pct: number;
  weekly_hours: number;
}

export type RoleStatus = "GREEN" | "YELLOW" | "RED";

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
