export interface Vendor {
  id: number;
  name: string;
  billing_type: string | null;
  hourly_rate: number | null;
  role_key: string | null;
  active: number;
}

export interface Invoice {
  id: number;
  month: string;
  msa_amount: number;
  tm_amount: number;
  total_amount: number;
  invoice_number: string | null;
  received_date: string | null;
  paid: number;
  notes: string | null;
}

export interface MonthlyCost {
  month: string;
  billing_type: string;
  total_hours: number;
  total_cost: number;
}

export interface ProjectCost {
  ete_project_id: string | null;
  ete_project_name: string | null;
  project_hours: number;
  support_hours: number;
  total_hours: number;
  total_cost: number;
  tm_cost: number;
  msa_hours: number;
  tm_hours: number;
}
