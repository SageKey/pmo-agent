import { useMemo, useState } from "react";
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
import { useTasks, useCompleteTask } from "@/hooks/useTasks";
import { cn } from "@/lib/cn";
import { shortDate, timeAgo } from "@/lib/format";
import type { Milestone } from "@/types/milestone";
import type { Task } from "@/types/task";

const PRIORITY_BG: Record<string, string> = {
  Highest: "bg-red-100 text-red-700",
  High: "bg-amber-100 text-amber-700",
  Medium: "bg-slate-100 text-slate-700",
  Low: "bg-slate-50 text-slate-500",
};

const STATUS_LABEL: Record<string, string> = {
  not_started: "Not started",
  in_progress: "Working",
  blocked: "Blocked",
  complete: "Complete",
};

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

  const loading = milestonesQuery.isLoading || tasksQuery.isLoading;

  return (
    <Card>
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
        <div>
          <div className="text-sm font-semibold text-slate-800">Project plan</div>
          <p className="mt-0.5 text-xs text-slate-500">
            Phases group related tasks. Click any task row to edit it.
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
  completedCount: number;
  hours: number;
  completedHours: number;
  /** Weighted by hours when available, otherwise falls back to count-based. */
  pctComplete: number;
  earliestStart: string | null;
  latestEnd: string | null;
}

function computeRollup(tasks: Task[]): PhaseRollup {
  let completedCount = 0;
  let hours = 0;
  let completedHours = 0;
  let earliestStart: string | null = null;
  let latestEnd: string | null = null;

  for (const t of tasks) {
    const status = t.status ?? "not_started";
    const isComplete = status === "complete";
    if (isComplete) completedCount += 1;

    const h = t.est_hours ?? 0;
    hours += h;
    if (isComplete) completedHours += h;

    if (t.start_date) {
      if (!earliestStart || t.start_date < earliestStart) earliestStart = t.start_date;
    }
    if (t.end_date) {
      if (!latestEnd || t.end_date > latestEnd) latestEnd = t.end_date;
    }
  }

  // Weighted by hours when we have them, otherwise count-based.
  const pctComplete =
    hours > 0
      ? completedHours / hours
      : tasks.length > 0
        ? completedCount / tasks.length
        : 0;

  return {
    count: tasks.length,
    completedCount,
    hours,
    completedHours,
    pctComplete,
    earliestStart,
    latestEnd,
  };
}

// ---------------------------------------------------------------------------
// PhaseSection — header + tasks
// ---------------------------------------------------------------------------

function PhaseSection({
  milestone,
  tasks,
  collapsed,
  onToggle,
  onAddTask,
  onEditTask,
  onCompleteTask,
}: {
  milestone: Milestone | null;
  tasks: Task[];
  collapsed: boolean;
  onToggle: () => void;
  onAddTask: () => void;
  onEditTask: (t: Task) => void;
  onCompleteTask: (taskId: number) => void;
}) {
  const title = milestone?.title ?? "Unassigned";
  const isUnassigned = milestone === null;
  const rollup = useMemo(() => computeRollup(tasks), [tasks]);

  return (
    <div>
      {/* Phase header with rollup strip */}
      <div
        className={cn(
          "flex items-center gap-4 px-5 py-3",
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

        {/* Rollup strip — always shown, with zero/empty fallbacks */}
        <PhaseRollupStrip rollup={rollup} />

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
// PhaseRollupStrip — always renders every stat with empty-state fallbacks
// ---------------------------------------------------------------------------

function PhaseRollupStrip({ rollup }: { rollup: PhaseRollup }) {
  const hasTasks = rollup.count > 0;

  return (
    <div className="flex items-center gap-3 text-[11px] text-slate-500">
      {/* Task count */}
      <span className="rounded-full bg-white px-2 py-0.5 font-bold tabular-nums text-slate-700 ring-1 ring-inset ring-slate-200">
        {rollup.count} {rollup.count === 1 ? "task" : "tasks"}
      </span>

      {/* Total hours — always shown */}
      <span className="tabular-nums">
        {hasTasks ? `${rollup.hours.toFixed(0)}h` : "— hrs"}
      </span>

      {/* Progress bar + % — always shown when there are tasks */}
      {hasTasks && (
        <div className="flex items-center gap-1.5">
          <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-200">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                rollup.pctComplete >= 1 ? "bg-emerald-500" : "bg-sky-500",
              )}
              style={{ width: `${Math.min(rollup.pctComplete * 100, 100)}%` }}
            />
          </div>
          <span className="tabular-nums font-semibold text-slate-700">
            {Math.round(rollup.pctComplete * 100)}%
          </span>
        </div>
      )}

      {/* Date range — always shown with placeholder */}
      <span className="tabular-nums">
        {rollup.earliestStart && rollup.latestEnd
          ? `${shortDate(rollup.earliestStart)} → ${shortDate(rollup.latestEnd)}`
          : "— dates"}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// TaskRow — fully static, click row to edit via modal
// ---------------------------------------------------------------------------

function TaskRow({
  task: t,
  delay,
  onEdit,
  onComplete,
}: {
  task: Task;
  delay: number;
  onEdit: () => void;
  onComplete: () => void;
}) {
  const status = t.status ?? "not_started";
  const StatusIcon = STATUS_ICON[status] ?? Circle;
  const isComplete = status === "complete";

  return (
    <motion.div
      initial={{ opacity: 0, x: -4 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2, delay }}
      onClick={onEdit}
      className="group grid cursor-pointer grid-cols-12 items-center gap-3 border-t border-slate-100 px-5 py-2 pl-12 text-sm hover:bg-slate-50"
    >
      {/* Title + complete checkbox */}
      <div className="col-span-4 flex items-center gap-2 min-w-0">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            if (!isComplete) onComplete();
          }}
          disabled={isComplete}
          className={cn(
            "shrink-0 text-slate-300 hover:text-emerald-500 transition-colors",
            isComplete && "text-emerald-500 cursor-default",
          )}
          title={isComplete ? "Completed" : "Mark complete"}
        >
          <StatusIcon className="h-4 w-4" />
        </button>
        <div className="min-w-0 flex-1">
          <div
            className={cn(
              "truncate font-medium text-slate-800",
              isComplete && "line-through text-slate-500",
            )}
          >
            {t.title}
          </div>
          {t.updated_at && t.updated_by && (
            <div
              className="mt-0.5 truncate text-[10px] text-slate-400"
              title={`Updated ${new Date(t.updated_at).toLocaleString()}`}
            >
              Updated by {t.updated_by} · {timeAgo(t.updated_at)}
            </div>
          )}
        </div>
      </div>

      {/* Assignee */}
      <div className="col-span-2 truncate text-xs text-slate-600">
        {t.assignee ?? "—"}
      </div>

      {/* Status */}
      <div className="col-span-2">
        <span
          className={cn(
            "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold",
            STATUS_BG[status] ?? STATUS_BG.not_started,
          )}
        >
          {STATUS_LABEL[status] ?? status}
        </span>
      </div>

      {/* Priority */}
      <div className="col-span-1">
        <span
          className={cn(
            "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold",
            PRIORITY_BG[t.priority ?? ""] ?? PRIORITY_BG.Medium,
          )}
        >
          {t.priority ?? "—"}
        </span>
      </div>

      {/* Dates */}
      <div className="col-span-2 text-[11px] text-slate-500 tabular-nums">
        {t.start_date || t.end_date ? (
          <>
            {t.start_date ? shortDate(t.start_date) : "—"}
            {" → "}
            {t.end_date ? shortDate(t.end_date) : "—"}
          </>
        ) : (
          "—"
        )}
      </div>

      {/* Hours */}
      <div className="col-span-1 flex items-center justify-end gap-2 text-xs tabular-nums text-slate-600">
        <span>{(t.est_hours ?? 0).toFixed(0)}h</span>
        <Pencil className="h-3 w-3 text-slate-300 opacity-0 transition-opacity group-hover:opacity-100" />
      </div>
    </motion.div>
  );
}
