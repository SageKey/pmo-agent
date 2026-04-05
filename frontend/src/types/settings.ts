export type SettingValueType = "float" | "int" | "bool" | "string";

export interface AppSetting {
  key: string;
  category: string;
  value: string;
  value_type: SettingValueType;
  label: string;
  description: string | null;
  min_value: number | null;
  max_value: number | null;
  unit: string | null;
  sort_order: number;
  updated_at: string | null;
  updated_by: string | null;
}
