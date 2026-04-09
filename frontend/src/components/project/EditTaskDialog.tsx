import { useEffect, useState } from "react";
import { Loader2, Trash2 } from "lucide-react";
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
  useCreateTask,
  useDeleteTask,
  useUpdateTask,
} from "@/hooks/useTasks";
import type { Task } from "@/types/task";
import type { Milestone } from "@/types/milestone";

const PRIORITY_OPTIONS = ["Highest", "High", "Medium", "Low"] as const;

const STATUS_OPTIONS = [
  { value: "not_started", label: "Not started" },
  { value: "in_progress", label: "In progress" },
  { value: "blocked", label: "Blocked" },
  { value: "complete", label: "Complete" },
] as const;

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: string;
  milestones: Milestone[];
  /** Pass a task to edit, or null/undefined to create. */
  task?: Task | null;
  /** Default milestone for new tasks. */
  defaultMilestoneId?: number | null;
}

type FormState = {
  title: string;
  milestone_id: string; // "" for unassigned
  assignee: string;
  priority: string;
  status: string;
  start_date: string;
  end_date: string;
  est_hours: string;
  description: string;
};

function blank(defaultMilestoneId?: number | null): FormState {
  return {
    title: "",
    milestone_id: defaultMilestoneId ? String(defaultMilestoneId) : "",
    assignee: "",
    priority: "Medium",
    status: "not_started",
    start_date: "",
    end_date: "",
    est_hours: "",
    description: "",
  };
}

function fromTask(t: Task): FormState {
  return {
    title: t.title ?? "",
    milestone_id: t.milestone_id ? String(t.milestone_id) : "",
    assignee: t.assignee ?? "",
    priority: t.priority ?? "Medium",
    status: t.status ?? "not_started",
    start_date: t.start_date ?? "",
    end_date: t.end_date ?? "",
    est_hours: t.est_hours?.toString() ?? "",
    description: t.description ?? "",
  };
}

export function EditTaskDialog({
  open,
  onOpenChange,
  projectId,
  milestones,
  task,
  defaultMilestoneId,
}: Props) {
  const isEdit = Boolean(task);
  const [form, setForm] = useState<FormState>(() => blank(defaultMilestoneId));
  const createMut = useCreateTask(projectId);
  const updateMut = useUpdateTask(projectId);
  const deleteMut = useDeleteTask(projectId);
  const mutation = isEdit ? updateMut : createMut;

  useEffect(() => {
    if (open) {
      setForm(task ? fromTask(task) : blank(defaultMilestoneId));
      createMut.reset();
      updateMut.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, task?.id, defaultMilestoneId]);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const canSubmit = form.title.trim() !== "";

  const handleSave = async () => {
    if (!canSubmit) return;
    const payload = {
      title: form.title.trim(),
      milestone_id: form.milestone_id ? parseInt(form.milestone_id) : null,
      assignee: form.assignee || null,
      priority: form.priority,
      status: form.status,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      est_hours: parseFloat(form.est_hours) || 0,
      description: form.description || null,
    };
    try {
      if (isEdit && task) {
        await updateMut.mutateAsync({
          id: task.id,
          project_id: projectId,
          ...payload,
        });
      } else {
        await createMut.mutateAsync(payload);
      }
      onOpenChange(false);
    } catch {
      /* surfaces via mutation.error */
    }
  };

  const handleDelete = async () => {
    if (!task) return;
    if (!confirm(`Delete task "${task.title}"? This cannot be undone.`)) return;
    try {
      await deleteMut.mutateAsync(task.id);
      onOpenChange(false);
    } catch {
      /* surfaces via mutation.error */
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit task" : "New task"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update the task details."
              : "Add a task to this project. Assign it to a phase to group it."}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-2">
          <Field label="Title">
            <Input
              value={form.title}
              onChange={(v) => set("title", v)}
              placeholder="What needs to happen?"
              autoFocus
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Phase">
              <select
                value={form.milestone_id}
                onChange={(e) => set("milestone_id", e.target.value)}
                className={selectCls}
              >
                <option value="">— no phase —</option>
                {milestones.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.title}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Assignee">
              <Input
                value={form.assignee}
                onChange={(v) => set("assignee", v)}
                placeholder="Who owns it?"
              />
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Status">
              <select
                value={form.status}
                onChange={(e) => set("status", e.target.value)}
                className={selectCls}
              >
                {STATUS_OPTIONS.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Priority">
              <select
                value={form.priority}
                onChange={(e) => set("priority", e.target.value)}
                className={selectCls}
              >
                {PRIORITY_OPTIONS.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <div className="grid grid-cols-3 gap-3">
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
            <Field label="Est. hours">
              <Input
                type="number"
                value={form.est_hours}
                onChange={(v) => set("est_hours", v)}
                min={0}
                placeholder="0"
              />
            </Field>
          </div>

          <Field label="Description">
            <textarea
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
              rows={2}
              placeholder="Optional context"
              className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
            />
          </Field>

          {mutation.isError && (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
              Failed: {(mutation.error as Error).message}
            </div>
          )}
        </div>

        <DialogFooter className="flex-row-reverse justify-between">
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={mutation.isPending}
            >
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={mutation.isPending || !canSubmit}>
              {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              {isEdit ? "Save changes" : "Create task"}
            </Button>
          </div>
          {isEdit && (
            <Button
              variant="ghost"
              onClick={handleDelete}
              disabled={deleteMut.isPending}
              className="text-red-600 hover:bg-red-50 hover:text-red-700"
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

const selectCls =
  "w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100";

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
