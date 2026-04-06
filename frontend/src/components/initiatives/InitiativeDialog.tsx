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
import { useCreateInitiative, useUpdateInitiative } from "@/hooks/useInitiatives";
import type { Initiative } from "@/types/initiative";

const PRIORITY_OPTIONS = ["Highest", "High", "Medium", "Low"] as const;
const STATUS_OPTIONS = ["Active", "On Hold", "Complete"] as const;

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Pass an existing initiative to edit. Omit for create mode. */
  initiative?: Initiative | null;
}

type FormState = {
  id: string;
  name: string;
  description: string;
  sponsor: string;
  status: string;
  it_involvement: boolean;
  priority: string;
  target_start: string;
  target_end: string;
};

function blank(): FormState {
  return {
    id: "",
    name: "",
    description: "",
    sponsor: "",
    status: "Active",
    it_involvement: false,
    priority: "Medium",
    target_start: "",
    target_end: "",
  };
}

function fromInitiative(i: Initiative): FormState {
  return {
    id: i.id,
    name: i.name,
    description: i.description ?? "",
    sponsor: i.sponsor ?? "",
    status: i.status,
    it_involvement: i.it_involvement,
    priority: i.priority ?? "Medium",
    target_start: i.target_start?.slice(0, 10) ?? "",
    target_end: i.target_end?.slice(0, 10) ?? "",
  };
}

export function InitiativeDialog({ open, onOpenChange, initiative }: Props) {
  const isEdit = Boolean(initiative);
  const [form, setForm] = useState<FormState>(blank);
  const createMut = useCreateInitiative();
  const updateMut = useUpdateInitiative();
  const mutation = isEdit ? updateMut : createMut;

  useEffect(() => {
    if (open) {
      setForm(initiative ? fromInitiative(initiative) : blank());
      createMut.reset();
      updateMut.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, initiative]);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const canSubmit = form.id.trim() !== "" && form.name.trim() !== "";

  const handleSave = async () => {
    if (!canSubmit) return;
    const payload = {
      id: form.id.trim(),
      name: form.name.trim(),
      description: form.description || null,
      sponsor: form.sponsor || null,
      status: form.status,
      it_involvement: form.it_involvement,
      priority: form.priority || null,
      target_start: form.target_start || null,
      target_end: form.target_end || null,
    };
    try {
      if (isEdit) {
        await updateMut.mutateAsync(payload);
      } else {
        await createMut.mutateAsync(payload as Parameters<typeof createMut.mutateAsync>[0]);
      }
      onOpenChange(false);
    } catch {
      /* error surfaces via mutation.error */
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit initiative" : "New initiative"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update the initiative details."
              : "Create a key business initiative. Link projects to it afterward."}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-2">
          <div className="grid grid-cols-[1fr_2fr] gap-3">
            <Field label="Initiative ID">
              <Input
                value={form.id}
                onChange={(v) => set("id", v)}
                placeholder="INIT-32"
                disabled={isEdit}
                autoFocus={!isEdit}
              />
            </Field>
            <Field label="Name">
              <Input
                value={form.name}
                onChange={(v) => set("name", v)}
                placeholder="Short, descriptive initiative name"
                autoFocus={isEdit}
              />
            </Field>
          </div>

          <Field label="Description">
            <textarea
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
              placeholder="What is this initiative about?"
              rows={2}
              className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Sponsor">
              <Input
                value={form.sponsor}
                onChange={(v) => set("sponsor", v)}
                placeholder="Executive sponsor"
              />
            </Field>
            <Field label="Priority">
              <select
                value={form.priority}
                onChange={(e) => set("priority", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              >
                {PRIORITY_OPTIONS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Status">
              <select
                value={form.status}
                onChange={(e) => set("status", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              >
                {STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </Field>
            <Field label="IT involvement">
              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  role="switch"
                  aria-checked={form.it_involvement}
                  onClick={() => set("it_involvement", !form.it_involvement)}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors ${
                    form.it_involvement ? "bg-sky-500" : "bg-slate-300"
                  }`}
                >
                  <span
                    className={`inline-block h-5 w-5 transform rounded-full bg-white shadow ring-1 ring-black/5 transition-transform ${
                      form.it_involvement ? "translate-x-5" : "translate-x-0.5"
                    }`}
                  />
                </button>
                <span className="text-sm text-slate-700">
                  {form.it_involvement ? "Yes — IT projects involved" : "No IT projects"}
                </span>
              </div>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Target start">
              <Input
                type="date"
                value={form.target_start}
                onChange={(v) => set("target_start", v)}
              />
            </Field>
            <Field label="Target end">
              <Input
                type="date"
                value={form.target_end}
                onChange={(v) => set("target_end", v)}
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
            {isEdit ? "Save changes" : "Create initiative"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
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
  value, onChange, type = "text", placeholder, min, autoFocus, disabled,
}: {
  value: string; onChange: (v: string) => void; type?: string;
  placeholder?: string; min?: number; autoFocus?: boolean; disabled?: boolean;
}) {
  return (
    <input
      type={type} value={value} onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder} min={min} autoFocus={autoFocus} disabled={disabled}
      className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100 disabled:opacity-50"
    />
  );
}
