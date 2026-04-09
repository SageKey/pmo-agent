import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  Circle,
  Clock,
  Ban,
  Pencil,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EditTaskDialog } from "@/components/project/EditTaskDialog";
import { useMilestones, useAddMilestone } from "@/hooks/useMilestones";
import { useTasks, useUpdateTask, useCompleteTask } from "@/hooks/useTasks";
import { cn } from "@/lib/cn";
import { shortDate } from "@/lib/format";
import type { Milestone } from "@/types/milestone";
import type { Task } from "@/types/task";

const PRIORITY_OPTIONS = ["Highest", "High", "Medium", "Low"] as const;

const PRIORITY_BG: Record<string, string> = {
  Highest: "bg-red-100 text-red-700",
  High: "bg-amber-100 text-amber-700",
  Medium: "bg-slate-100 text-slate-700",
  Low: "bg-slate-50 text-slate-500",
};

const STATUS_OPTIONS = [
  { value: "not_started", label: "Not started" },
  { value: "in_progress", label: "Working" },
  { value: "blocked", label: "Blocked" },
  { value: "complete", label: "Complete" },
] as const;

const STATUS_LABEL: Record<string, string> = Object.fromEntries(
  STATUS_OPTIONS.map((s) => [s.value, s.label]),
);

const STATUS_BG: Record<string, string> = {
  not_started: "bg-slate-100 text-slate-600",
  in_progress: "bg-sky-100 text-sky-700",
  blocked: "bg-red-100 text-red-700",
  complete: "bg-emerald-100 text-emerald-700",
};

const STATUS_ICON: Record<string, React.ComponentType<{ className?: string }>> = {
  not_started: Circle,
  in_progress: Clock,
  blocked: Ban,
  complete: CheckCircle2,
};

export function PlanPanel({ projectId }: { projectId: string }) {
  const milestonesQuery = useMilestones(projectId);
  const tasksQuery = useTasks(projectId);
  const createMilestone = useAddMilestone(projectId);
  const completeTask = useCompleteTask(projectId);
  const updateTask = useUpdateTask(projectId);

  const milestones = milestonesQuery.data ?? [];
  const tasks = tasksQuery.data ?? [];

  // Group tasks by milestone_id. Unassigned under a synthetic null bucket.
  const groups = useMemo(() => {
    const byMilestone = new Map<number | null, Task[]>();
    byMilestone.set(null, []);
    for (const m of milestones) byMilestone.set(m.id, []);
    for (const t of tasks) {
      const key = t.milestone_id ?? null;
      if (!byMilestone.has(key)) byMilestone.set(key, []);
      byMilestone.get(key)!.push(t);
    }
    for (const arr of byMilestone.values()) {
      arr.sort((a, b) => {
        const so = (a.sort_order ?? 0) - (b.sort_order ?? 0);
        if (so !== 0) return so;
        return a.title.localeCompare(b.title);
      });
    }
    return byMilestone;
  }, [milestones, tasks]);

  const [collapsed, setCollapsed] = useState<Set<number | null>>(new Set());
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editTask, setEditTask] = useState<Task | null>(null);
  const [defaultMilestoneId, setDefaultMilestoneId] = useState<number | null>(null);

  const toggleCollapse = (id: number | null) => {
    setCollapsed((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const openNewTask = (milestoneId: number | null) => {
    setEditTask(null);
    setDefaultMilestoneId(milestoneId);
    setDialogOpen(true);
  };

  const openEditTask = (task: Task) => {
    setEditTask(task);
    setDefaultMilestoneId(null);
    setDialogOpen(true);
  };

  const handleAddPhase = async () => {
    const title = prompt("Phase name (e.g. Discovery, Planning, Execution):");
    if (!title?.trim()) return;
    try {
      await createMilestone.mutateAsync({
        title: title.trim(),
        milestone_type: "deliverable",
        sort_order: milestones.length,
      });
    } catch {
      alert("Failed to create phase");
    }
  };

  // Inline edit handler — partial update, merges with task's current values
  const handleInlineUpdate = (task: Task, patch: Partial<Task>) => {
    updateTask.mutate({
      id: task.id,
      project_id: projectId,
      ...patch,
    });
  };

  const loading = milestonesQuery.isLoading || tasksQuery.isLoading;

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
        <div>
          <div className="text-sm font-semibold text-slate-800">Project plan</div>
          <p className="mt-0.5 text-xs text-slate-500">
            Phases group related tasks. Click any cell to edit inline.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleAddPhase}
            disabled={createMilestone.isPending}
          >
            <Plus className="h-3.5 w-3.5" />
            Add phase
          </Button>
          <Button size="sm" onClick={() => openNewTask(null)}>
            <Plus className="h-3.5 w-3.5" />
            Add task
          </Button>
        </div>
      </div>

      {loading && (
        <div className="px-5 py-12 text-center text-sm text-slate-500">
          Loading plan…
        </div>
      )}

      {!loading && milestones.length === 0 && tasks.length === 0 && (
        <div className="px-5 py-12 text-center text-sm text-slate-500">
          No phases or tasks yet. Click <strong>Add phase</strong> to create
          your first one.
        </div>
      )}

      {!loading && (milestones.length > 0 || tasks.length > 0) && (
        <div className="divide-y divide-slate-100">
          {milestones.map((m) => {
            const phaseTasks = groups.get(m.id) ?? [];
            return (
              <PhaseSection
                key={m.id}
                milestone={m}
                tasks={phaseTasks}
                collapsed={collapsed.has(m.id)}
                onToggle={() => toggleCollapse(m.id)}
                onAddTask={() => openNewTask(m.id)}
                onEditTask={openEditTask}
                onCompleteTask={(id) => completeTask.mutate(id)}
                onInlineUpdate={handleInlineUpdate}
              />
            );
          })}
          {(groups.get(null)?.length ?? 0) > 0 && (
            <PhaseSection
              milestone={null}
              tasks={groups.get(null) ?? []}
              collapsed={collapsed.has(null)}
              onToggle={() => toggleCollapse(null)}
              onAddTask={() => openNewTask(null)}
              onEditTask={openEditTask}
              onCompleteTask={(id) => completeTask.mutate(id)}
              onInlineUpdate={handleInlineUpdate}
            />
          )}
        </div>
      )}

      <EditTaskDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        projectId={projectId}
        milestones={milestones}
        task={editTask}
        defaultMilestoneId={defaultMilestoneId}
      />
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Phase rollup calculation
// ---------------------------------------------------------------------------

interface PhaseRollup {
  count: number;
  hours: number;
  completedHours: number;
  pctComplete: number; // 0-1
  earliestStart: string | null;
  latestEnd: string | null;
  statusCounts: Record<string, number>;
}

function computeRollup(tasks: Task[]): PhaseRollup {
  const statusCounts: Record<string, number> = {};
  let hours = 0;
  let completedHours = 0;
  let earliestStart: string | null = null;
  let latestEnd: string | null = null;

  for (const t of tasks) {
    const status = t.status ?? "not_started";
    statusCounts[status] = (statusCounts[status] ?? 0) + 1;
    const h = t.est_hours ?? 0;
    hours += h;
    if (status === "complete") completedHours += h;

    if (t.start_date) {
      if (!earliestStart || t.start_date < earliestStart) earliestStart = t.start_date;
    }
    if (t.end_date) {
      if (!latestEnd || t.end_date > latestEnd) latestEnd = t.end_date;
    }
  }

  return {
    count: tasks.length,
    hours,
    completedHours,
    pctComplete: hours > 0 ? completedHours / hours : 0,
    earliestStart,
    latestEnd,
    statusCounts,
  };
}

// ---------------------------------------------------------------------------
// PhaseSection
// ---------------------------------------------------------------------------

function PhaseSection({
  milestone,
  tasks,
  collapsed,
  onToggle,
  onAddTask,
  onEditTask,
  onCompleteTask,
  onInlineUpdate,
}: {
  milestone: Milestone | null;
  tasks: Task[];
  collapsed: boolean;
  onToggle: () => void;
  onAddTask: () => void;
  onEditTask: (t: Task) => void;
  onCompleteTask: (taskId: number) => void;
  onInlineUpdate: (task: Task, patch: Partial<Task>) => void;
}) {
  const title = milestone?.title ?? "Unassigned";
  const isUnassigned = milestone === null;
  const rollup = useMemo(() => computeRollup(tasks), [tasks]);

  return (
    <div>
      {/* Phase header with rollup strip */}
      <div
        className={cn(
          "flex items-center gap-3 px-5 py-2.5",
          isUnassigned ? "bg-slate-50/50" : "bg-slate-50",
        )}
      >
        <button
          type="button"
          onClick={onToggle}
          className="text-slate-400 hover:text-slate-600"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </button>
        <div
          className={cn(
            "text-sm font-semibold",
            isUnassigned ? "italic text-slate-500" : "text-slate-800",
          )}
        >
          {title}
        </div>
        {milestone?.due_date && (
          <span className="text-[11px] text-slate-500">
            Due {shortDate(milestone.due_date)}
          </span>
        )}
        {/* Rollup stats */}
        {rollup.count > 0 && (
          <div className="flex items-center gap-3 text-[11px] text-slate-600">
            <span className="rounded-full bg-white px-2 py-0.5 font-bold tabular-nums ring-1 ring-inset ring-slate-200">
              {rollup.count} {rollup.count === 1 ? "task" : "tasks"}
            </span>
            {rollup.hours > 0 && (
              <span className="tabular-nums">
                {rollup.hours.toFixed(0)}h
              </span>
            )}
            {rollup.hours > 0 && (
              <div className="flex items-center gap-1.5">
                <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-200">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all",
                      rollup.pctComplete >= 1 ? "bg-emerald-500" : "bg-sky-500",
                    )}
                    style={{ width: `${Math.min(rollup.pctComplete * 100, 100)}%` }}
                  />
                </div>
                <span className="tabular-nums font-semibold">
                  {Math.round(rollup.pctComplete * 100)}%
                </span>
              </div>
            )}
            {rollup.earliestStart && rollup.latestEnd && (
              <span className="tabular-nums text-slate-500">
                {shortDate(rollup.earliestStart)} → {shortDate(rollup.latestEnd)}
              </span>
            )}
          </div>
        )}
        <div className="ml-auto">
          <Button
            variant="ghost"
            size="sm"
            onClick={onAddTask}
            className="h-7 text-[11px] text-slate-600 hover:text-navy-700"
          >
            <Plus className="h-3 w-3" />
            Task
          </Button>
        </div>
      </div>

      {!collapsed && (
        <>
          {tasks.length === 0 ? (
            <div className="px-12 py-3 text-xs italic text-slate-400">
              No tasks yet.
            </div>
          ) : (
            <>
              {/* Column headers */}
              <div className="grid grid-cols-12 gap-3 border-t border-slate-100 bg-slate-50/30 px-5 py-1.5 pl-12 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                <div className="col-span-4">Task</div>
                <div className="col-span-2">Assignee</div>
                <div className="col-span-2">Status</div>
                <div className="col-span-1">Priority</div>
                <div className="col-span-2">Dates</div>
                <div className="col-span-1 text-right">Hours</div>
              </div>
              {tasks.map((t, i) => (
                <TaskRow
                  key={t.id}
                  task={t}
                  delay={i * 0.02}
                  onEdit={() => onEditTask(t)}
                  onComplete={() => onCompleteTask(t.id)}
                  onInlineUpdate={(patch) => onInlineUpdate(t, patch)}
                />
              ))}
            </>
          )}
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// TaskRow with inline editing
// ---------------------------------------------------------------------------

function TaskRow({
  task: t,
  delay,
  onEdit,
  onComplete,
  onInlineUpdate,
}: {
  task: Task;
  delay: number;
  onEdit: () => void;
  onComplete: () => void;
  onInlineUpdate: (patch: Partial<Task>) => void;
}) {
  const status = t.status ?? "not_started";
  const StatusIcon = STATUS_ICON[status] ?? Circle;
  const isComplete = status === "complete";

  return (
    <motion.div
      initial={{ opacity: 0, x: -4 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2, delay }}
      className="group grid grid-cols-12 items-center gap-3 border-t border-slate-100 px-5 py-2 pl-12 text-sm hover:bg-slate-50"
    >
      {/* Title + complete checkbox */}
      <div className="col-span-4 flex items-center gap-2 min-w-0">
        <button
          type="button"
          onClick={onComplete}
          disabled={isComplete}
          className={cn(
            "shrink-0 text-slate-300 hover:text-emerald-500 transition-colors",
            isComplete && "text-emerald-500 cursor-default",
          )}
          title={isComplete ? "Completed" : "Mark complete"}
        >
          <StatusIcon className="h-4 w-4" />
        </button>
        <InlineText
          value={t.title}
          onSave={(v) => v && v !== t.title && onInlineUpdate({ title: v })}
          className={cn(
            "flex-1 truncate font-medium text-slate-800",
            isComplete && "line-through text-slate-500",
          )}
        />
      </div>

      {/* Assignee */}
      <div className="col-span-2 min-w-0">
        <InlineText
          value={t.assignee ?? ""}
          placeholder="—"
          onSave={(v) => onInlineUpdate({ assignee: v || null })}
          className="truncate text-xs text-slate-600"
        />
      </div>

      {/* Status — inline dropdown */}
      <div className="col-span-2">
        <InlineSelect
          value={status}
          options={STATUS_OPTIONS.map((o) => ({ value: o.value, label: o.label }))}
          onSave={(v) => onInlineUpdate({ status: v })}
          pillClass={cn(
            "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold",
            STATUS_BG[status] ?? STATUS_BG.not_started,
          )}
        >
          {STATUS_LABEL[status] ?? status}
        </InlineSelect>
      </div>

      {/* Priority — inline dropdown */}
      <div className="col-span-1">
        <InlineSelect
          value={t.priority ?? "Medium"}
          options={PRIORITY_OPTIONS.map((p) => ({ value: p, label: p }))}
          onSave={(v) => onInlineUpdate({ priority: v })}
          pillClass={cn(
            "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold",
            PRIORITY_BG[t.priority ?? ""] ?? PRIORITY_BG.Medium,
          )}
        >
          {t.priority ?? "—"}
        </InlineSelect>
      </div>

      {/* Dates — inline date inputs */}
      <div className="col-span-2 flex items-center gap-1 text-[11px] text-slate-500 tabular-nums">
        <InlineDate
          value={t.start_date ?? ""}
          onSave={(v) => onInlineUpdate({ start_date: v || null })}
          display={t.start_date ? shortDate(t.start_date) : "—"}
        />
        <span className="text-slate-300">→</span>
        <InlineDate
          value={t.end_date ?? ""}
          onSave={(v) => onInlineUpdate({ end_date: v || null })}
          display={t.end_date ? shortDate(t.end_date) : "—"}
        />
      </div>

      {/* Hours */}
      <div className="col-span-1 flex items-center justify-end gap-2 text-xs tabular-nums text-slate-600">
        <InlineNumber
          value={t.est_hours ?? 0}
          onSave={(v) => onInlineUpdate({ est_hours: v })}
          suffix="h"
        />
        <button
          type="button"
          onClick={onEdit}
          className="opacity-0 transition-opacity group-hover:opacity-100 text-slate-400 hover:text-navy-700"
          title="Edit full task"
        >
          <Pencil className="h-3 w-3" />
        </button>
      </div>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Inline editor primitives
// ---------------------------------------------------------------------------

function InlineText({
  value,
  placeholder,
  onSave,
  className,
}: {
  value: string;
  placeholder?: string;
  onSave: (v: string) => void;
  className?: string;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => setDraft(value), [value]);
  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  const commit = () => {
    setEditing(false);
    if (draft !== value) onSave(draft);
  };

  if (editing) {
    return (
      <input
        ref={inputRef}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit();
          if (e.key === "Escape") {
            setDraft(value);
            setEditing(false);
          }
        }}
        className={cn(
          "rounded-sm border border-sky-400 bg-white px-1 outline-none ring-1 ring-sky-200",
          className,
        )}
      />
    );
  }

  return (
    <button
      type="button"
      onClick={() => setEditing(true)}
      className={cn("cursor-pointer text-left hover:bg-slate-100 rounded-sm px-1", className)}
    >
      {value || placeholder || "—"}
    </button>
  );
}

function InlineSelect({
  value,
  options,
  onSave,
  pillClass,
  children,
}: {
  value: string;
  options: { value: string; label: string }[];
  onSave: (v: string) => void;
  pillClass: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Click outside to close
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className={cn(pillClass, "cursor-pointer hover:brightness-95")}
      >
        {children}
      </button>
      {open && (
        <div className="absolute left-0 top-full z-10 mt-1 min-w-[120px] rounded-md border border-slate-200 bg-white py-1 shadow-lg">
          {options.map((o) => (
            <button
              key={o.value}
              type="button"
              onClick={() => {
                if (o.value !== value) onSave(o.value);
                setOpen(false);
              }}
              className={cn(
                "block w-full px-3 py-1.5 text-left text-xs hover:bg-slate-50",
                o.value === value && "font-semibold text-navy-700",
              )}
            >
              {o.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function InlineDate({
  value,
  onSave,
  display,
}: {
  value: string;
  onSave: (v: string) => void;
  display: string;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => setDraft(value), [value]);
  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  const commit = () => {
    setEditing(false);
    if (draft !== value) onSave(draft);
  };

  if (editing) {
    return (
      <input
        ref={inputRef}
        type="date"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit();
          if (e.key === "Escape") {
            setDraft(value);
            setEditing(false);
          }
        }}
        className="rounded-sm border border-sky-400 bg-white px-1 text-[11px] outline-none ring-1 ring-sky-200"
      />
    );
  }

  return (
    <button
      type="button"
      onClick={() => setEditing(true)}
      className="cursor-pointer rounded-sm px-1 hover:bg-slate-100"
    >
      {display}
    </button>
  );
}

function InlineNumber({
  value,
  onSave,
  suffix,
}: {
  value: number;
  onSave: (v: number) => void;
  suffix?: string;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(String(value));
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => setDraft(String(value)), [value]);
  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  const commit = () => {
    setEditing(false);
    const n = parseFloat(draft);
    if (!Number.isNaN(n) && n !== value) onSave(n);
  };

  if (editing) {
    return (
      <input
        ref={inputRef}
        type="number"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit();
          if (e.key === "Escape") {
            setDraft(String(value));
            setEditing(false);
          }
        }}
        min={0}
        className="w-14 rounded-sm border border-sky-400 bg-white px-1 text-right text-xs outline-none ring-1 ring-sky-200"
      />
    );
  }

  return (
    <button
      type="button"
      onClick={() => setEditing(true)}
      className="cursor-pointer rounded-sm px-1 hover:bg-slate-100"
    >
      {value.toFixed(0)}
      {suffix}
    </button>
  );
}
