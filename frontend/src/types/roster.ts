export interface TeamMember {
  name: string;
  role: string;
  role_key: string;
  team: string | null;
  vendor: string | null;
  classification: string | null;
  rate_per_hour: number;
  weekly_hrs_available: number;
  support_reserve_pct: number;
  project_capacity_pct: number;
  project_capacity_hrs: number;
  include_in_capacity: boolean;
}

export interface PersonProjectDemand {
  project_id: string;
  project_name: string;
  role_key: string;
  weekly_hours: number;
  alloc_pct: number;
}

export type RoleStatus = "BLUE" | "GREEN" | "YELLOW" | "RED";

export interface PersonDemand {
  name: string;
  role: string;
  role_key: string;
  total_weekly_hrs: number;
  capacity_hrs: number;
  utilization_pct: number;
  status: RoleStatus;
  project_count: number;
  projects: PersonProjectDemand[];
  include_in_capacity: boolean;
}
