import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import type { Milestone } from "@/types/milestone";
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
  useAddMilestone,
  useUpdateMilestone,
  type MilestoneCreatePayload,
} from "@/hooks/useMilestones";

const TYPE_OPTIONS = [
  { value: "deliverable", label: "Deliverable" },
  { value: "gate", label: "Gate" },
  { value: "decision", label: "Decision" },
  { value: "review", label: "Review" },
  { value: "checkpoint", label: "Checkpoint" },
  { value: "go_live", label: "Go-live" },
];

const STATUS_OPTIONS = [
  { value: "not_started", label: "Not started" },
  { value: "in_progress", label: "In progress" },
  { value: "blocked", label: "Blocked" },
  { value: "complete", label: "Complete" },
];

interface Props {
  projectId: string;
  /** null/undefined = create mode. Passed milestone = edit mode. */
  milestone: Milestone | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type FormState = {
  title: string;
  milestone_type: string;
  status: string;
  due_date: string;
  owner: string;
  progress_pct: string;
  notes: string;
};

function blank(): FormState {
  return {
    title: "",
    milestone_type: "deliverable",
    status: "not_started",
    due_date: "",
    owner: "",
    progress_pct: "0",
    notes: "",
  };
}

function fromMilestone(m: Milestone): FormState {
  return {
    title: m.title ?? "",
    milestone_type: m.milestone_type ?? "deliverable",
    status: m.status ?? "not_started",
    due_date: m.due_date ?? "",
    owner: m.owner ?? "",
    progress_pct: (m.progress_pct ?? 0).toString(),
    notes: m.notes ?? "",
  };
}

export function EditMilestoneDialog({
  projectId,
  milestone,
  open,
  onOpenChange,
}: Props) {
  const isEdit = milestone !== null;
  const [form, setForm] = useState<FormState>(
    milestone ? fromMilestone(milestone) : blank(),
  );

  const addMutation = useAddMilestone(projectId);
  const updateMutation = useUpdateMilestone(projectId);
  const mutation = isEdit ? updateMutation : addMutation;

  useEffect(() => {
    if (open) {
      setForm(milestone ? fromMilestone(milestone) : blank());
      addMutation.reset();
      updateMutation.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, milestone?.id]);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const handleSave = async () => {
    const base: MilestoneCreatePayload = {
      title: form.title.trim(),
      milestone_type: form.milestone_type,
      status: form.status,
      due_date: form.due_date || null,
      owner: form.owner || null,
      progress_pct: Number.parseFloat(form.progress_pct) || 0,
      notes: form.notes || null,
    };
    if (!base.title) return;

    try {
      if (isEdit && milestone) {
        await updateMutation.mutateAsync({
          id: milestone.id,
          payload: { ...base, project_id: projectId },
        });
      } else {
        await addMutation.mutateAsync(base);
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
          <DialogTitle>{isEdit ? "Edit milestone" : "Add milestone"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update the milestone details and click Save."
              : "Create a new gate, deliverable, or decision point."}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-2">
          <Field label="Title">
            <input
              type="text"
              value={form.title}
              onChange={(e) => set("title", e.target.value)}
              placeholder="e.g. Design Review"
              autoFocus
              className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Type">
              <select
                value={form.milestone_type}
                onChange={(e) => set("milestone_type", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              >
                {TYPE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Status">
              <select
                value={form.status}
                onChange={(e) => set("status", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              >
                {STATUS_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Due date">
              <input
                type="date"
                value={form.due_date}
                onChange={(e) => set("due_date", e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
            </Field>
            <Field label="Owner">
              <input
                type="text"
                value={form.owner}
                onChange={(e) => set("owner", e.target.value)}
                placeholder="Optional"
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
            </Field>
          </div>

          <Field label="Notes">
            <textarea
              value={form.notes}
              onChange={(e) => set("notes", e.target.value)}
              placeholder="Optional context"
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
          <Button
            onClick={handleSave}
            disabled={mutation.isPending || !form.title.trim()}
          >
            {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            {isEdit ? "Save" : "Add milestone"}
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
