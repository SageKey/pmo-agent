import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import type { Invoice } from "@/types/financials";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  useCreateInvoice,
  useUpdateInvoice,
  type InvoicePayload,
} from "@/hooks/useFinancials";

interface Props {
  /** null = create mode, Invoice = edit mode */
  invoice: Invoice | null;
  /** Pre-fills month in create mode */
  defaultMonth: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type FormState = {
  month: string;
  msa_amount: string;
  tm_amount: string;
  invoice_number: string;
  received_date: string;
  paid: boolean;
  notes: string;
};

function blank(month: string): FormState {
  return {
    month,
    msa_amount: "0",
    tm_amount: "0",
    invoice_number: "",
    received_date: "",
    paid: false,
    notes: "",
  };
}

function fromInvoice(inv: Invoice): FormState {
  return {
    month: inv.month,
    msa_amount: inv.msa_amount.toString(),
    tm_amount: inv.tm_amount.toString(),
    invoice_number: inv.invoice_number ?? "",
    received_date: inv.received_date ?? "",
    paid: Boolean(inv.paid),
    notes: inv.notes ?? "",
  };
}

export function InvoiceDialog({
  invoice,
  defaultMonth,
  open,
  onOpenChange,
}: Props) {
  const isEdit = invoice !== null;
  const [form, setForm] = useState<FormState>(() =>
    invoice ? fromInvoice(invoice) : blank(defaultMonth),
  );
  const createMutation = useCreateInvoice();
  const updateMutation = useUpdateInvoice();
  const mutation = isEdit ? updateMutation : createMutation;

  useEffect(() => {
    if (open) {
      setForm(invoice ? fromInvoice(invoice) : blank(defaultMonth));
      createMutation.reset();
      updateMutation.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, invoice?.id, defaultMonth]);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const msa = Number.parseFloat(form.msa_amount) || 0;
  const tm = Number.parseFloat(form.tm_amount) || 0;
  const total = msa + tm;

  const handleSave = async () => {
    const payload: InvoicePayload = {
      month: form.month,
      msa_amount: msa,
      tm_amount: tm,
      total_amount: total,
      invoice_number: form.invoice_number || null,
      received_date: form.received_date || null,
      paid: form.paid ? 1 : 0,
      notes: form.notes || null,
    };
    try {
      if (isEdit && invoice) {
        await updateMutation.mutateAsync({ id: invoice.id, payload });
      } else {
        await createMutation.mutateAsync(payload);
      }
      onOpenChange(false);
    } catch {
      /* error surfaces via mutation.error */
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit invoice" : "New invoice"}</DialogTitle>
          <DialogDescription>
            Vendor invoices are tracked by month with MSA + T&M split.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-2">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Month (YYYY-MM)">
              <input
                type="text"
                value={form.month}
                onChange={(e) => set("month", e.target.value)}
                placeholder="2026-04"
                pattern="\d{4}-\d{2}"
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
            </Field>
            <Field label="Invoice #">
              <input
                type="text"
                value={form.invoice_number}
                onChange={(e) => set("invoice_number", e.target.value)}
                placeholder="INV-123"
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="MSA amount">
              <MoneyInput
                value={form.msa_amount}
                onChange={(v) => set("msa_amount", v)}
              />
            </Field>
            <Field label="T&M amount">
              <MoneyInput
                value={form.tm_amount}
                onChange={(v) => set("tm_amount", v)}
              />
            </Field>
          </div>

          <div className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-600">
            Total:{" "}
            <span className="font-semibold tabular-nums text-slate-900">
              ${total.toLocaleString()}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Received date">
              <input
                type="date"
                value={form.received_date}
                onChange={(e) => set("received_date", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
            </Field>
            <Field label="Status">
              <label className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.paid}
                  onChange={(e) => set("paid", e.target.checked)}
                  className="h-4 w-4 accent-emerald-500"
                />
                <span className="text-slate-700">Paid</span>
              </label>
            </Field>
          </div>

          <Field label="Notes">
            <textarea
              value={form.notes}
              onChange={(e) => set("notes", e.target.value)}
              placeholder="Optional"
              rows={2}
              className="w-full resize-none rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
            />
          </Field>

          {mutation.isError && (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
              Failed: {(mutation.error as Error).message}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={mutation.isPending}
          >
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={mutation.isPending}>
            {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            {isEdit ? "Save" : "Create invoice"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block text-xs">
      <span className="mb-1 block font-semibold uppercase tracking-wider text-slate-500">
        {label}
      </span>
      {children}
    </label>
  );
}

function MoneyInput({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="relative">
      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">
        $
      </span>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        min={0}
        className="w-full rounded-md border border-slate-200 bg-white py-2 pl-7 pr-3 text-right text-sm tabular-nums text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
      />
    </div>
  );
}
