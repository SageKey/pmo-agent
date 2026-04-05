import { useEffect, useState } from "react";
import { Archive, Loader2, Trash2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import type { Project } from "@/types/project";
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
  useDeleteProject,
  useUpdateProject,
  type ProjectPatch,
} from "@/hooks/usePortfolio";
import { cn } from "@/lib/cn";

const PRIORITY_OPTIONS = ["Highest", "High", "Medium", "Low"] as const;

const HEALTH_OPTIONS = [
  "🟢 ON TRACK",
  "🟡 AT RISK",
  "🔴 NEEDS HELP",
  "⚪ NOT STARTED",
  "🔵 NEEDS FUNCTIONAL SPEC",
  "🔵 NEEDS TECHNICAL SPEC",
  "✅ COMPLETE",
  "⏸️ POSTPONED",
];

const ROLE_KEYS = [
  "pm",
  "ba",
  "functional",
  "technical",
  "developer",
  "infrastructure",
  "dba",
  "wms",
] as const;

const ROLE_LABEL: Record<string, string> = {
  pm: "Project Manager",
  ba: "Business Analyst",
  functional: "Functional",
  technical: "Technical",
  developer: "Developer",
  infrastructure: "Infrastructure",
  dba: "DBA",
  wms: "WMS",
};

interface Props {
  project: Project;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type FormState = {
  name: string;
  priority: string;
  health: string;
  pm: string;
  portfolio: string;
  start_date: string;
  end_date: string;
  est_hours: string;
  pct_complete: string;
  budget: string;
  notes: string;
};

function projectToForm(p: Project): FormState {
  return {
    name: p.name ?? "",
    priority: p.priority ?? "Medium",
    health: p.health ?? "",
    pm: p.pm ?? "",
    portfolio: p.portfolio ?? "",
    start_date: p.start_date ?? "",
    end_date: p.end_date ?? "",
    est_hours: p.est_hours?.toString() ?? "0",
    pct_complete: ((p.pct_complete ?? 0) * 100).toFixed(0),
    budget: p.budget?.toString() ?? "0",
    notes: p.notes ?? "",
  };
}

/** Backend stores allocations as 0–1 fractions. UI edits 0–100 ints. */
function allocsToForm(p: Project): Record<string, string> {
  const out: Record<string, string> = {};
  for (const key of ROLE_KEYS) {
    const frac = p.role_allocations?.[key] ?? 0;
    out[key] = Math.round(frac * 100).toString();
  }
  return out;
}

export function EditProjectDialog({ project, open, onOpenChange }: Props) {
  const [tab, setTab] = useState<"details" | "allocations">("details");
  const [form, setForm] = useState<FormState>(() => projectToForm(project));
  const [allocs, setAllocs] = useState<Record<string, string>>(() =>
    allocsToForm(project),
  );
  const mutation = useUpdateProject(project.id);
  const deleteMutation = useDeleteProject();
  const navigate = useNavigate();

  useEffect(() => {
    if (open) {
      setTab("details");
      setForm(projectToForm(project));
      setAllocs(allocsToForm(project));
      mutation.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, project.id]);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const setAlloc = (roleKey: string, pct: string) => {
    setAllocs((a) => ({ ...a, [roleKey]: pct }));
  };

  const handleArchive = async () => {
    if (
      !confirm(
        `Archive "${project.name}"? It will be marked POSTPONED and moved to the Archive group.`,
      )
    )
      return;
    try {
      await mutation.mutateAsync({ health: "⏸️ POSTPONED" });
      onOpenChange(false);
    } catch {
      /* error surfaces via mutation.error */
    }
  };

  const handleDelete = async () => {
    if (
      !confirm(
        `Permanently delete "${project.name}" (${project.id})? This removes all milestones, comments, assignments, and audit history. Cannot be undone.`,
      )
    )
      return;
    try {
      await deleteMutation.mutateAsync(project.id);
      onOpenChange(false);
      navigate("/portfolio");
    } catch {
      /* error surfaces via mutation.error */
    }
  };

  const handleSave = async () => {
    const roleAllocations: Record<string, number> = {};
    for (const key of ROLE_KEYS) {
      const pct = Number.parseFloat(allocs[key]) || 0;
      roleAllocations[key] = Math.max(0, Math.min(1, pct / 100));
    }

    const patch: ProjectPatch = {
      name: form.name,
      priority: form.priority || null,
      health: form.health || null,
      pm: form.pm || null,
      portfolio: form.portfolio || null,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      est_hours: Number.parseFloat(form.est_hours) || 0,
      pct_complete: Math.max(
        0,
        Math.min(1, (Number.parseFloat(form.pct_complete) || 0) / 100),
      ),
      budget: Number.parseFloat(form.budget) || 0,
      notes: form.notes || null,
      role_allocations: roleAllocations,
    };
    try {
      await mutation.mutateAsync(patch);
      onOpenChange(false);
    } catch {
      /* error surfaces via mutation.error */
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Edit project</DialogTitle>
          <DialogDescription>
            <span className="font-mono">{project.id}</span> · changes save when you
            click Save.
          </DialogDescription>
        </DialogHeader>

        {/* Tabs */}
        <div className="flex gap-1 border-b border-slate-200">
          <TabButton active={tab === "details"} onClick={() => setTab("details")}>
            Details
          </TabButton>
          <TabButton
            active={tab === "allocations"}
            onClick={() => setTab("allocations")}
          >
            Role allocations
          </TabButton>
        </div>

        {tab === "details" && (
          <div className="grid gap-4 py-2">
            <Field label="Project name">
              <TextInput
                value={form.name}
                onChange={(v) => set("name", v)}
                placeholder="Project name"
              />
            </Field>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Priority">
                <Select
                  value={form.priority}
                  onChange={(v) => set("priority", v)}
                  options={PRIORITY_OPTIONS.map((p) => ({ value: p, label: p }))}
                />
              </Field>
              <Field label="Health">
                <Select
                  value={form.health}
                  onChange={(v) => set("health", v)}
                  options={HEALTH_OPTIONS.map((h) => ({ value: h, label: h }))}
                  allowEmpty
                />
              </Field>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Field label="PM">
                <TextInput
                  value={form.pm}
                  onChange={(v) => set("pm", v)}
                  placeholder="Project manager"
                />
              </Field>
              <Field label="Business portfolio">
                <TextInput
                  value={form.portfolio}
                  onChange={(v) => set("portfolio", v)}
                  placeholder="e.g. Sales & Distribution"
                />
              </Field>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Start date">
                <TextInput
                  type="date"
                  value={form.start_date}
                  onChange={(v) => set("start_date", v)}
                />
              </Field>
              <Field label="End date">
                <TextInput
                  type="date"
                  value={form.end_date}
                  onChange={(v) => set("end_date", v)}
                />
              </Field>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <Field label="Est. hours">
                <TextInput
                  type="number"
                  value={form.est_hours}
                  onChange={(v) => set("est_hours", v)}
                  min={0}
                />
              </Field>
              <Field label="% complete">
                <TextInput
                  type="number"
                  value={form.pct_complete}
                  onChange={(v) => set("pct_complete", v)}
                  min={0}
                  max={100}
                  suffix="%"
                />
              </Field>
              <Field label="Budget">
                <TextInput
                  type="number"
                  value={form.budget}
                  onChange={(v) => set("budget", v)}
                  min={0}
                  prefix="$"
                />
              </Field>
            </div>

            <Field label="Notes">
              <textarea
                value={form.notes}
                onChange={(e) => set("notes", e.target.value)}
                placeholder="Optional notes or context"
                rows={3}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
            </Field>
          </div>
        )}

        {tab === "allocations" && (
          <div className="py-2">
            <div className="mb-3 text-xs text-slate-500">
              Percentage of project hours consumed by each role. Drives capacity
              calculations. Does not need to sum to 100%.
            </div>
            <div className="grid gap-3">
              {ROLE_KEYS.map((key) => (
                <AllocRow
                  key={key}
                  label={ROLE_LABEL[key]}
                  value={allocs[key] ?? "0"}
                  onChange={(v) => setAlloc(key, v)}
                />
              ))}
            </div>
          </div>
        )}

        {mutation.isError && (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
            Failed to save: {(mutation.error as Error).message}
          </div>
        )}

        <DialogFooter className="!justify-between">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleArchive}
              disabled={mutation.isPending || deleteMutation.isPending}
              title="Mark project as postponed"
            >
              <Archive className="h-4 w-4" />
              Archive
            </Button>
            <Button
              variant="outline"
              onClick={handleDelete}
              disabled={mutation.isPending || deleteMutation.isPending}
              className="text-red-700 hover:bg-red-50"
              title="Permanently delete"
            >
              {deleteMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
              Delete
            </Button>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={mutation.isPending}
            >
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={mutation.isPending}>
              {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Save changes
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "relative px-4 py-2 text-sm font-medium transition-colors",
        active ? "text-slate-900" : "text-slate-500 hover:text-slate-700",
      )}
    >
      {children}
      {active && (
        <span className="absolute inset-x-2 bottom-0 h-0.5 rounded-t bg-navy-900" />
      )}
    </button>
  );
}

function AllocRow({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  const pct = Math.max(0, Math.min(100, Number.parseFloat(value) || 0));
  return (
    <div className="flex items-center gap-3">
      <div className="w-36 shrink-0 text-sm font-medium text-slate-700">{label}</div>
      <div className="flex-1">
        <input
          type="range"
          min={0}
          max={100}
          step={5}
          value={pct}
          onChange={(e) => onChange(e.target.value)}
          className="w-full accent-navy-900"
        />
      </div>
      <div className="relative w-20 shrink-0">
        <input
          type="number"
          min={0}
          max={100}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-md border border-slate-200 bg-white py-1.5 pl-2 pr-7 text-right text-sm tabular-nums text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
        />
        <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-xs text-slate-400">
          %
        </span>
      </div>
    </div>
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

function TextInput({
  value,
  onChange,
  type = "text",
  placeholder,
  min,
  max,
  prefix,
  suffix,
}: {
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  min?: number;
  max?: number;
  prefix?: string;
  suffix?: string;
}) {
  return (
    <div className="relative">
      {prefix && (
        <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">
          {prefix}
        </span>
      )}
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        min={min}
        max={max}
        className={`w-full rounded-md border border-slate-200 bg-white py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100 ${
          prefix ? "pl-7" : "pl-3"
        } ${suffix ? "pr-8" : "pr-3"}`}
      />
      {suffix && (
        <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">
          {suffix}
        </span>
      )}
    </div>
  );
}

function Select({
  value,
  onChange,
  options,
  allowEmpty = false,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  allowEmpty?: boolean;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
    >
      {allowEmpty && <option value="">—</option>}
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}
