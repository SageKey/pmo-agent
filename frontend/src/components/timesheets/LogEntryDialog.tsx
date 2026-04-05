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
import { useVendors } from "@/hooks/useFinancials";
import {
  useCreateTimesheetEntry,
  type TimesheetEntryPayload,
} from "@/hooks/useTimesheets";

interface Props {
  /** Defaults entry_date into this month so users don't have to type it. */
  defaultMonth: string; // "YYYY-MM"
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type FormState = {
  consultant_id: string;
  entry_date: string;
  project_key: string;
  project_name: string;
  task_description: string;
  work_type: string;
  hours: string;
};

function todayIn(month: string): string {
  const [y, m] = month.split("-").map(Number);
  const today = new Date();
  if (today.getFullYear() === y && today.getMonth() + 1 === m) {
    return today.toISOString().slice(0, 10);
  }
  // Otherwise default to the 1st of the month
  return `${month}-01`;
}

export function LogEntryDialog({ defaultMonth, open, onOpenChange }: Props) {
  const vendors = useVendors(true);
  const mutation = useCreateTimesheetEntry();

  const [form, setForm] = useState<FormState>(() => ({
    consultant_id: "",
    entry_date: todayIn(defaultMonth),
    project_key: "",
    project_name: "",
    task_description: "",
    work_type: "Project",
    hours: "8",
  }));

  useEffect(() => {
    if (open) {
      setForm({
        consultant_id: vendors.data?.[0]?.id?.toString() ?? "",
        entry_date: todayIn(defaultMonth),
        project_key: "",
        project_name: "",
        task_description: "",
        work_type: "Project",
        hours: "8",
      });
      mutation.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, defaultMonth, vendors.data?.length]);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const canSubmit =
    form.consultant_id !== "" &&
    form.entry_date !== "" &&
    Number.parseFloat(form.hours) > 0;

  const handleSave = async () => {
    if (!canSubmit) return;
    const payload: TimesheetEntryPayload = {
      consultant_id: Number.parseInt(form.consultant_id, 10),
      entry_date: form.entry_date,
      project_key: form.project_key || null,
      project_name: form.project_name || null,
      task_description: form.task_description || null,
      work_type: form.work_type,
      hours: Number.parseFloat(form.hours) || 0,
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
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Log timesheet entry</DialogTitle>
          <DialogDescription>
            Record hours worked by a vendor consultant against a project or
            support category.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-2">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Consultant">
              <select
                value={form.consultant_id}
                onChange={(e) => set("consultant_id", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              >
                <option value="">Select…</option>
                {(vendors.data ?? []).map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name} ({v.billing_type})
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Date">
              <input
                type="date"
                value={form.entry_date}
                onChange={(e) => set("entry_date", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Project key">
              <input
                type="text"
                value={form.project_key}
                onChange={(e) => set("project_key", e.target.value)}
                placeholder="PRJ-001"
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
            </Field>
            <Field label="Project name">
              <input
                type="text"
                value={form.project_name}
                onChange={(e) => set("project_name", e.target.value)}
                placeholder="Optional"
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Work type">
              <select
                value={form.work_type}
                onChange={(e) => set("work_type", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              >
                <option value="Project">Project</option>
                <option value="Support">Support</option>
              </select>
            </Field>
            <Field label="Hours">
              <input
                type="number"
                value={form.hours}
                onChange={(e) => set("hours", e.target.value)}
                min={0}
                max={24}
                step={0.25}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-right text-sm tabular-nums text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
            </Field>
          </div>

          <Field label="Task description">
            <input
              type="text"
              value={form.task_description}
              onChange={(e) => set("task_description", e.target.value)}
              placeholder="Optional"
              className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
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
          <Button
            onClick={handleSave}
            disabled={mutation.isPending || !canSubmit}
          >
            {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Log entry
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
