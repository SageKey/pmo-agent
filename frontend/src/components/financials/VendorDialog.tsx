import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useUpsertVendor, type VendorPayload } from "@/hooks/useFinancials";

const ROLE_OPTIONS = [
  { key: "pm", label: "Project Manager" },
  { key: "ba", label: "Business Analyst" },
  { key: "functional", label: "Functional" },
  { key: "technical", label: "Technical" },
  { key: "developer", label: "Developer" },
  { key: "infrastructure", label: "Infrastructure" },
  { key: "dba", label: "DBA" },
  { key: "erp", label: "ERP" },
];

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type FormState = {
  name: string;
  billing_type: string;
  hourly_rate: string;
  role_key: string;
  active: boolean;
};

const blank = (): FormState => ({
  name: "",
  billing_type: "T&M",
  hourly_rate: "",
  role_key: "developer",
  active: true,
});

export function VendorDialog({ open, onOpenChange }: Props) {
  const [form, setForm] = useState<FormState>(blank);
  const mutation = useUpsertVendor();

  useEffect(() => {
    if (open) {
      setForm(blank());
      mutation.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const canSubmit = form.name.trim() !== "";

  const handleSave = async () => {
    if (!canSubmit) return;
    const payload: VendorPayload = {
      name: form.name.trim(),
      billing_type: form.billing_type,
      hourly_rate: Number.parseFloat(form.hourly_rate) || 0,
      role_key: form.role_key || null,
      active: form.active ? 1 : 0,
    };
    try {
      await mutation.mutateAsync(payload);
      onOpenChange(false);
    } catch {
      /* error surfaces via mutation.error */
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>New vendor consultant</DialogTitle>
          <DialogDescription>
            Used for timesheet entry lookup and billing calculations.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-2">
          <Field label="Name">
            <input
              type="text"
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="Consultant name"
              autoFocus
              className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Billing type">
              <select
                value={form.billing_type}
                onChange={(e) => set("billing_type", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              >
                <option value="T&M">T&M (hourly)</option>
                <option value="MSA">MSA (retainer)</option>
              </select>
            </Field>
            <Field label="Role">
              <select
                value={form.role_key}
                onChange={(e) => set("role_key", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              >
                {ROLE_OPTIONS.map((r) => (
                  <option key={r.key} value={r.key}>
                    {r.label}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <Field label="Hourly rate">
            <div className="relative">
              <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">
                $
              </span>
              <input
                type="number"
                value={form.hourly_rate}
                onChange={(e) => set("hourly_rate", e.target.value)}
                min={0}
                placeholder="0"
                className="w-full rounded-md border border-slate-200 bg-white py-2 pl-7 pr-10 text-right text-sm tabular-nums text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">
                /hr
              </span>
            </div>
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
          <Button
            onClick={handleSave}
            disabled={mutation.isPending || !canSubmit}
          >
            {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Add vendor
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
