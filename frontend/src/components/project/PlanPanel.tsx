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
import { shortDate } from "@/lib/format";
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

  // Group tasks by milestone_id. Unassigned tasks live under a synthetic
  // "No phase" bucket so they're still visible and editable.
  const groups = useMemo(() => {
    const byMilestone = new Map<number | null, Task[]>();
    byMilestone.set(null, []);
    for (const m of milestones) byMilestone.set(m.id, []);
    for (const t of tasks) {
      const key = t.milestone_id ?? null;
      if (!byMilestone.has(key)) byMilestone.set(key, []);
      byMilestone.get(key)!.push(t);
    }
    // Sort tasks within each group by sort_order then title
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
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
        <div>
          <div className="text-sm font-semibold text-slate-800">Project plan</div>
          <p className="mt-0.5 text-xs text-slate-500">
            Phases group related tasks. Add tasks under a phase or leave them
            unassigned.
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
          {/* Phases with their tasks */}
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

          {/* Unassigned tasks — only show if there are any */}
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

  return (
    <div>
      {/* Phase header */}
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
        <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-bold tabular-nums text-slate-500 ring-1 ring-inset ring-slate-200">
          {tasks.length}
        </span>
        {milestone?.due_date && (
          <span className="text-[11px] text-slate-500">
            Due {shortDate(milestone.due_date)}
          </span>
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

      {/* Tasks — hidden when collapsed */}
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
        <button
          type="button"
          onClick={onEdit}
          className={cn(
            "truncate text-left font-medium text-slate-800 hover:text-navy-700",
            isComplete && "line-through text-slate-500",
          )}
        >
          {t.title}
        </button>
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
        <span>{t.est_hours?.toFixed(0) ?? "0"}h</span>
        <button
          type="button"
          onClick={onEdit}
          className="opacity-0 transition-opacity group-hover:opacity-100 text-slate-400 hover:text-navy-700"
          title="Edit"
        >
          <Pencil className="h-3 w-3" />
        </button>
      </div>
    </motion.div>
  );
}
