import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Invoice, MonthlyCost, ProjectCost, Vendor } from "@/types/financials";

export function useVendors(activeOnly = true) {
  return useQuery({
    queryKey: ["financials", "vendors", activeOnly],
    queryFn: async () => {
      const { data } = await api.get<Vendor[]>("/financials/vendors", {
        params: { active_only: activeOnly },
      });
      return data;
    },
  });
}

export function useInvoices(year: number) {
  return useQuery({
    queryKey: ["financials", "invoices", year],
    queryFn: async () => {
      const { data } = await api.get<Invoice[]>("/financials/invoices", {
        params: { year },
      });
      return data;
    },
  });
}

export function useMonthlyCosts(year: number) {
  return useQuery({
    queryKey: ["financials", "monthly", year],
    queryFn: async () => {
      const { data } = await api.get<MonthlyCost[]>("/financials/monthly", {
        params: { year },
      });
      return data;
    },
  });
}

export function useProjectCosts(year: number) {
  return useQuery({
    queryKey: ["financials", "by-project", year],
    queryFn: async () => {
      const { data } = await api.get<ProjectCost[]>("/financials/by-project", {
        params: { year },
      });
      return data;
    },
  });
}
