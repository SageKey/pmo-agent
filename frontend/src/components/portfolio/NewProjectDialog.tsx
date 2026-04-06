import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useCreateProject, type ProjectCreatePayload } from "@/hooks/usePortfolio";
import { useInitiatives } from "@/hooks/useInitiatives";

const PRIORITY_OPTIONS = ["Highest", "High", "Medium", "Low"] as const;

const HEALTH_OPTIONS = [
  "🟢 ON TRACK",
  "🟡 AT RISK",
  "🔴 NEEDS HELP",
  "⚪ NOT STARTED",
  "🔵 NEEDS FUNCTIONAL SPEC",
  "🔵 NEEDS TECHNICAL SPEC",
  "📋 PIPELINE",
];

const QUARTER_OPTIONS = [
  "2026-Q1", "2026-Q2", "2026-Q3", "2026-Q4",
  "2027-Q1", "2027-Q2", "2027-Q3", "2027-Q4",
];

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type FormState = {
  id: string;
  name: string;
  priority: string;
  health: string;
  pm: string;
  portfolio: string;
  start_date: string;
  end_date: string;
  est_hours: string;
  budget: string;
  initiative_id: string;
  planned_it_start: string;
};

function blank(): FormState {
  return {
    id: "",
    name: "",
    priority: "Medium",
    health: "⚪ NOT STARTED",
    pm: "",
    portfolio: "",
    start_date: "",
    end_date: "",
    est_hours: "",
    budget: "",
    initiative_id: "",
    planned_it_start: "",
  };
}

export function NewProjectDialog({ open, onOpenChange }: Props) {
  const [form, setForm] = useState<FormState>(blank);
  const mutation = useCreateProject();
  const initQuery = useInitiatives();
  const initiatives = initQuery.data ?? [];
  const navigate = useNavigate();

  useEffect(() => {
    if (open) {
      setForm(blank());
      mutation.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const canSubmit = form.id.trim() !== "" && form.name.trim() !== "";

  const handleSave = async () => {
    if (!canSubmit) return;
    const payload: ProjectCreatePayload = {
      id: form.id.trim(),
      name: form.name.trim(),
      priority: form.priority || null,
      health: form.health || null,
      pm: form.pm || null,
      portfolio: form.portfolio || null,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      est_hours: Number.parseFloat(form.est_hours) || 0,
      budget: Number.parseFloat(form.budget) || 0,
      initiative_id: form.initiative_id || null,
      planned_it_start: form.planned_it_start || null,
    };
    try {
      const created = await mutation.mutateAsync(payload);
      onOpenChange(false);
      navigate(`/portfolio/${created.id}`);
    } catch {
      /* error surfaces via mutation.error */
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>New project</DialogTitle>
          <DialogDescription>
            Create a project. You can edit details and role allocations after.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-2">
          <div className="grid grid-cols-[1fr_2fr] gap-3">
            <Field label="Project ID">
              <Input
                value={form.id}
                onChange={(v) => set("id", v)}
                placeholder="PRJ-123"
                autoFocus
              />
            </Field>
            <Field label="Name">
              <Input
                value={form.name}
                onChange={(v) => set("name", v)}
                placeholder="Short, descriptive project name"
              />
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Priority">
              <select
                value={form.priority}
                onChange={(e) => set("priority", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              >
                {PRIORITY_OPTIONS.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Health">
              <select
                value={form.health}
                onChange={(e) => set("health", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              >
                {HEALTH_OPTIONS.map((h) => (
                  <option key={h} value={h}>
                    {h}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="PM">
              <Input
                value={form.pm}
                onChange={(v) => set("pm", v)}
                placeholder="Project manager"
              />
            </Field>
            <Field label="Business portfolio">
              <Input
                value={form.portfolio}
                onChange={(v) => set("portfolio", v)}
                placeholder="e.g. Sales & Distribution"
              />
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Start date">
              <Input
                type="date"
                value={form.start_date}
                onChange={(v) => set("start_date", v)}
              />
            </Field>
            <Field label="End date">
              <Input
                type="date"
                value={form.end_date}
                onChange={(v) => set("end_date", v)}
              />
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Initiative (optional)">
              <select
                value={form.initiative_id}
                onChange={(e) => set("initiative_id", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              >
                <option value="">— none —</option>
                {initiatives.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.id} · {i.name}
                  </option>
                ))}
              </select>
            </Field>
            {form.health.includes("PIPELINE") && (
              <Field label="Planned IT start">
                <select
                  value={form.planned_it_start}
                  onChange={(e) => set("planned_it_start", e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
                >
                  <option value="">— select quarter —</option>
                  {QUARTER_OPTIONS.map((q) => (
                    <option key={q} value={q}>{q}</option>
                  ))}
                </select>
              </Field>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Est. hours">
              <Input
                type="number"
                value={form.est_hours}
                onChange={(v) => set("est_hours", v)}
                min={0}
                placeholder="0"
              />
            </Field>
            <Field label="Budget (optional)">
              <Input
                type="number"
                value={form.budget}
                onChange={(v) => set("budget", v)}
                min={0}
                placeholder="0"
              />
            </Field>
          </div>

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
            Create project
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

function Input({
  value,
  onChange,
  type = "text",
  placeholder,
  min,
  autoFocus,
}: {
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  min?: number;
  autoFocus?: boolean;
}) {
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      min={min}
      autoFocus={autoFocus}
      className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
    />
  );
}
