import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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

export interface InvoicePayload {
  month: string;
  msa_amount: number;
  tm_amount: number;
  total_amount?: number;
  invoice_number?: string | null;
  received_date?: string | null;
  paid: number;
  notes?: string | null;
}

export function useCreateInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: InvoicePayload) => {
      const { data } = await api.post<Invoice>(
        "/financials/invoices",
        payload,
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["financials"] });
    },
  });
}

export function useUpdateInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      payload,
    }: {
      id: number;
      payload: InvoicePayload;
    }) => {
      const { data } = await api.put<Invoice>(
        `/financials/invoices/${id}`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["financials"] });
    },
  });
}

export interface VendorPayload {
  name: string;
  billing_type: string;
  hourly_rate: number;
  role_key?: string | null;
  active: number;
}

export function useUpsertVendor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: VendorPayload) => {
      const { data } = await api.post<Vendor>(
        "/financials/vendors",
        payload,
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["financials"] });
      qc.invalidateQueries({ queryKey: ["timesheets"] });
    },
  });
}
