import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import type { TeamMember } from "@/types/roster";
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
  useCreateMember,
  useUpdateMember,
  type RosterMemberPayload,
} from "@/hooks/useRoster";

const ROLE_OPTIONS: { key: string; label: string; role: string }[] = [
  { key: "pm", label: "Project Manager", role: "Project Manager" },
  { key: "ba", label: "Business Analyst", role: "Business Analyst" },
  { key: "functional", label: "Functional", role: "Functional" },
  { key: "technical", label: "Technical", role: "Technical" },
  { key: "developer", label: "Developer", role: "Developer" },
  { key: "infrastructure", label: "Infrastructure", role: "Infrastructure" },
  { key: "dba", label: "DBA", role: "DBA" },
  { key: "erp", label: "ERP", role: "ERP Consultant" },
];

interface Props {
  /** null = create mode, TeamMember = edit mode */
  member: TeamMember | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type FormState = {
  name: string;
  role_key: string;
  team: string;
  vendor: string;
  classification: string;
  rate_per_hour: string;
  weekly_hrs_available: string;
  support_reserve_pct: string;
  include_in_capacity: boolean;
};

function blank(): FormState {
  return {
    name: "",
    role_key: "developer",
    team: "",
    vendor: "",
    classification: "FTE",
    rate_per_hour: "0",
    weekly_hrs_available: "40",
    support_reserve_pct: "0",
    include_in_capacity: true,
  };
}

function fromMember(m: TeamMember): FormState {
  return {
    name: m.name,
    role_key: m.role_key,
    team: m.team ?? "",
    vendor: m.vendor ?? "",
    classification: m.classification ?? "FTE",
    rate_per_hour: m.rate_per_hour.toString(),
    weekly_hrs_available: m.weekly_hrs_available.toString(),
    // support_reserve_pct is 0..1 in DB, show as 0..100
    support_reserve_pct: Math.round(m.support_reserve_pct * 100).toString(),
    include_in_capacity: m.include_in_capacity,
  };
}

export function EditMemberDialog({ member, open, onOpenChange }: Props) {
  const isEdit = member !== null;
  const [form, setForm] = useState<FormState>(() =>
    member ? fromMember(member) : blank(),
  );
  const createMutation = useCreateMember();
  const updateMutation = useUpdateMember();
  const mutation = isEdit ? updateMutation : createMutation;

  useEffect(() => {
    if (open) {
      setForm(member ? fromMember(member) : blank());
      createMutation.reset();
      updateMutation.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, member?.name]);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const canSubmit = form.name.trim() !== "";

  const handleSave = async () => {
    if (!canSubmit) return;
    const roleOption = ROLE_OPTIONS.find((r) => r.key === form.role_key);
    const payload: RosterMemberPayload = {
      name: form.name.trim(),
      role: roleOption?.role ?? form.role_key,
      role_key: form.role_key,
      team: form.team || null,
      vendor: form.vendor || null,
      classification: form.classification || null,
      rate_per_hour: Number.parseFloat(form.rate_per_hour) || 0,
      weekly_hrs_available: Number.parseFloat(form.weekly_hrs_available) || 0,
      support_reserve_pct: Math.max(
        0,
        Math.min(1, (Number.parseFloat(form.support_reserve_pct) || 0) / 100),
      ),
      include_in_capacity: form.include_in_capacity,
    };
    try {
      if (isEdit && member) {
        await updateMutation.mutateAsync({ originalName: member.name, payload });
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
          <DialogTitle>{isEdit ? "Edit member" : "Add team member"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update this person's capacity, rate, or role."
              : "Add a new person to the team roster."}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-2">
          <Field label="Name">
            <input
              type="text"
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="Full name"
              disabled={isEdit}
              autoFocus={!isEdit}
              className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100 disabled:bg-slate-50 disabled:text-slate-500"
            />
            {isEdit && (
              <div className="mt-1 text-[11px] text-slate-500">
                Names are immutable — delete and recreate to rename.
              </div>
            )}
          </Field>

          <div className="grid grid-cols-2 gap-3">
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
            <Field label="Classification">
              <select
                value={form.classification}
                onChange={(e) => set("classification", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              >
                <option value="FTE">FTE</option>
                <option value="Contractor">Contractor</option>
                <option value="Vendor">Vendor</option>
              </select>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Team">
              <input
                type="text"
                value={form.team}
                onChange={(e) => set("team", e.target.value)}
                placeholder="Optional"
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
            </Field>
            <Field label="Vendor">
              <input
                type="text"
                value={form.vendor}
                onChange={(e) => set("vendor", e.target.value)}
                placeholder="Optional (for contractors)"
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
            </Field>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Field label="Weekly hours">
              <NumberInput
                value={form.weekly_hrs_available}
                onChange={(v) => set("weekly_hrs_available", v)}
                min={0}
                max={80}
                suffix="hrs"
              />
            </Field>
            <Field label="Support reserve">
              <NumberInput
                value={form.support_reserve_pct}
                onChange={(v) => set("support_reserve_pct", v)}
                min={0}
                max={100}
                suffix="%"
              />
            </Field>
            <Field label="Rate">
              <NumberInput
                value={form.rate_per_hour}
                onChange={(v) => set("rate_per_hour", v)}
                min={0}
                prefix="$"
              />
            </Field>
          </div>

          <label className="flex items-start gap-3 rounded-md border border-slate-200 bg-slate-50 p-3">
            <input
              type="checkbox"
              checked={form.include_in_capacity}
              onChange={(e) => set("include_in_capacity", e.target.checked)}
              className="mt-0.5 h-4 w-4 shrink-0 accent-navy-900"
            />
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium text-slate-900">
                Include in capacity calculations
              </div>
              <div className="mt-0.5 text-[11px] text-slate-500">
                When unchecked, this person stays on the Team Roster for
                reference but their hours don't count toward role supply,
                utilization %, or the even-split demand fallback. Useful for
                leads or cross-functional roles who appear in the roster
                but don't actively take on work in their listed role.
              </div>
            </div>
          </label>

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
            {isEdit ? "Save" : "Add member"}
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

function NumberInput({
  value,
  onChange,
  min,
  max,
  prefix,
  suffix,
}: {
  value: string;
  onChange: (v: string) => void;
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
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        min={min}
        max={max}
        className={`w-full rounded-md border border-slate-200 bg-white py-2 text-sm tabular-nums text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100 ${
          prefix ? "pl-7" : "pl-3"
        } ${suffix ? "pr-10" : "pr-3"}`}
      />
      {suffix && (
        <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">
          {suffix}
        </span>
      )}
    </div>
  );
}
