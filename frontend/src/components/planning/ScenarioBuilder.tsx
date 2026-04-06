import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  FolderPlus,
  Ban,
  UserMinus,
  UserPlus,
  Trash2,
  Plus,
  X,
  CalendarRange,
  SlidersHorizontal,
  Scale,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/cn";
import type { ScenarioModification } from "@/types/scenario";
import type { Project } from "@/types/project";
import type { TeamMember } from "@/types/roster";

const ROLE_OPTIONS = [
  { key: "pm", label: "Project Manager" },
  { key: "ba", label: "Business Analyst" },
  { key: "functional", label: "Functional" },
  { key: "technical", label: "Technical" },
  { key: "developer", label: "Developer" },
  { key: "infrastructure", label: "Infrastructure" },
  { key: "dba", label: "DBA" },
  { key: "erp", label: "ERP" },
];

type BuilderMode = "closed" | "add_project" | "cancel_project" | "exclude_person" | "add_person" | "shift_project" | "change_allocation" | "resize_project";

export function ScenarioBuilder({
  modifications,
  onChange,
  projects,
  roster,
}: {
  modifications: ScenarioModification[];
  onChange: (mods: ScenarioModification[]) => void;
  projects: Project[];
  roster: TeamMember[];
}) {
  const [mode, setMode] = useState<BuilderMode>("closed");

  const addMod = (mod: ScenarioModification) => {
    onChange([...modifications, mod]);
    setMode("closed");
  };

  const removeMod = (idx: number) => {
    onChange(modifications.filter((_, i) => i !== idx));
  };

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div>
          <div className="text-sm font-semibold text-slate-800">
            Scenario modifications
          </div>
          <p className="mt-0.5 text-xs text-slate-500">
            Stack any combination. Engine re-runs in milliseconds.
          </p>
        </div>
        {modifications.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onChange([])}
            className="text-slate-500 hover:text-red-600"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Clear all
          </Button>
        )}
      </div>

      <CardContent className="space-y-3 p-4">
        {/* Existing modification chips */}
        <AnimatePresence initial={false}>
          {modifications.map((mod, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: -12 }}
              transition={{ duration: 0.2 }}
            >
              <ModificationChip mod={mod} onRemove={() => removeMod(idx)} />
            </motion.div>
          ))}
        </AnimatePresence>

        {modifications.length === 0 && mode === "closed" && (
          <div className="rounded-md border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
            No modifications yet. Add one below to see the impact.
          </div>
        )}

        {/* Inline editor based on selected mode */}
        {mode === "add_project" && (
          <AddProjectForm onCancel={() => setMode("closed")} onSubmit={addMod} />
        )}
        {mode === "cancel_project" && (
          <CancelProjectForm
            projects={projects}
            excludedIds={new Set(
              modifications
                .filter((m): m is Extract<ScenarioModification, { type: "cancel_project" }> => m.type === "cancel_project")
                .map((m) => m.project_id),
            )}
            onCancel={() => setMode("closed")}
            onSubmit={addMod}
          />
        )}
        {mode === "exclude_person" && (
          <ExcludePersonForm
            roster={roster}
            excludedNames={new Set(
              modifications
                .filter((m): m is Extract<ScenarioModification, { type: "exclude_person" }> => m.type === "exclude_person")
                .map((m) => m.person_name),
            )}
            onCancel={() => setMode("closed")}
            onSubmit={addMod}
          />
        )}
        {mode === "add_person" && (
          <AddPersonForm onCancel={() => setMode("closed")} onSubmit={addMod} />
        )}
        {mode === "shift_project" && (
          <ShiftProjectForm
            projects={projects}
            onCancel={() => setMode("closed")}
            onSubmit={addMod}
          />
        )}
        {mode === "change_allocation" && (
          <ChangeAllocationForm
            projects={projects}
            onCancel={() => setMode("closed")}
            onSubmit={addMod}
          />
        )}
        {mode === "resize_project" && (
          <ResizeProjectForm
            projects={projects}
            onCancel={() => setMode("closed")}
            onSubmit={addMod}
          />
        )}

        {/* Add-modification buttons */}
        {mode === "closed" && (
          <div className="grid grid-cols-2 gap-2 pt-2">
            <AddButton
              icon={<FolderPlus className="h-4 w-4" />}
              label="Add project"
              onClick={() => setMode("add_project")}
            />
            <AddButton
              icon={<Ban className="h-4 w-4" />}
              label="Cancel project"
              onClick={() => setMode("cancel_project")}
            />
            <AddButton
              icon={<UserMinus className="h-4 w-4" />}
              label="Exclude person"
              onClick={() => setMode("exclude_person")}
            />
            <AddButton
              icon={<UserPlus className="h-4 w-4" />}
              label="Add hire"
              onClick={() => setMode("add_person")}
            />
            <AddButton
              icon={<CalendarRange className="h-4 w-4" />}
              label="Shift dates"
              onClick={() => setMode("shift_project")}
            />
            <AddButton
              icon={<SlidersHorizontal className="h-4 w-4" />}
              label="Change allocation"
              onClick={() => setMode("change_allocation")}
            />
            <AddButton
              icon={<Scale className="h-4 w-4" />}
              label="Resize scope"
              onClick={() => setMode("resize_project")}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------

function AddButton({
  icon,
  label,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2.5 text-sm font-medium text-slate-700 transition-all hover:border-navy-300 hover:bg-navy-50 hover:text-navy-700"
    >
      <span className="text-slate-400 group-hover:text-navy-500">{icon}</span>
      {label}
    </button>
  );
}

function ModificationChip({
  mod,
  onRemove,
}: {
  mod: ScenarioModification;
  onRemove: () => void;
}) {
  const { icon, title, subtitle, tone } = describeModification(mod);
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-md border px-3 py-2.5",
        tone,
      )}
    >
      <div className="mt-0.5 shrink-0">{icon}</div>
      <div className="min-w-0 flex-1">
        <div className="text-sm font-semibold">{title}</div>
        <div className="mt-0.5 text-xs opacity-80">{subtitle}</div>
      </div>
      <button
        type="button"
        onClick={onRemove}
        className="shrink-0 rounded-md p-1 text-slate-400 hover:bg-white hover:text-red-600"
        aria-label="Remove modification"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

function describeModification(mod: ScenarioModification): {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  tone: string;
} {
  if (mod.type === "add_project") {
    const roles = Object.entries(mod.project.role_allocations)
      .filter(([, v]) => v > 0)
      .map(([k, v]) => `${k} ${Math.round(v * 100)}%`)
      .join(" · ");
    return {
      icon: <FolderPlus className="h-4 w-4 text-sky-600" />,
      title: `Add: ${mod.project.name}`,
      subtitle: `${mod.project.est_hours} hrs · ${mod.project.start_date} → ${mod.project.end_date} · ${roles || "no roles"}`,
      tone: "border-sky-200 bg-sky-50 text-sky-900",
    };
  }
  if (mod.type === "cancel_project") {
    return {
      icon: <Ban className="h-4 w-4 text-red-600" />,
      title: `Cancel: ${mod.project_id}`,
      subtitle: "Removes from active portfolio",
      tone: "border-red-200 bg-red-50 text-red-900",
    };
  }
  if (mod.type === "exclude_person") {
    return {
      icon: <UserMinus className="h-4 w-4 text-amber-600" />,
      title: `Exclude: ${mod.person_name}`,
      subtitle: "Removes their capacity from the calculation",
      tone: "border-amber-200 bg-amber-50 text-amber-900",
    };
  }
  if (mod.type === "add_person") {
    return {
      icon: <UserPlus className="h-4 w-4 text-emerald-600" />,
      title: `Hire: ${mod.person.name}`,
      subtitle: `${mod.person.role_key} · ${mod.person.weekly_hrs_available}h/week`,
      tone: "border-emerald-200 bg-emerald-50 text-emerald-900",
    };
  }
  if (mod.type === "shift_project") {
    const parts: string[] = [];
    if (mod.new_start_date) parts.push(`start → ${mod.new_start_date}`);
    if (mod.new_end_date) parts.push(`end → ${mod.new_end_date}`);
    return {
      icon: <CalendarRange className="h-4 w-4 text-violet-600" />,
      title: `Shift: ${mod.project_id}`,
      subtitle: parts.join(" · ") || "dates unchanged",
      tone: "border-violet-200 bg-violet-50 text-violet-900",
    };
  }
  if (mod.type === "change_allocation") {
    return {
      icon: <SlidersHorizontal className="h-4 w-4 text-indigo-600" />,
      title: `Realloc: ${mod.project_id}`,
      subtitle: `${mod.role_key} → ${Math.round(mod.allocation * 100)}%`,
      tone: "border-indigo-200 bg-indigo-50 text-indigo-900",
    };
  }
  // resize_project
  return {
    icon: <Scale className="h-4 w-4 text-teal-600" />,
    title: `Resize: ${mod.project_id}`,
    subtitle: `${mod.est_hours} estimated hours`,
    tone: "border-teal-200 bg-teal-50 text-teal-900",
  };
}

// ---------------------------------------------------------------------------
// Inline forms
// ---------------------------------------------------------------------------

function FormShell({
  title,
  onCancel,
  children,
}: {
  title: string;
  onCancel: () => void;
  children: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      className="overflow-hidden rounded-md border border-navy-200 bg-navy-50/30"
    >
      <div className="flex items-center justify-between border-b border-navy-200/60 px-3 py-2">
        <div className="text-xs font-semibold uppercase tracking-wider text-navy-700">
          {title}
        </div>
        <button
          type="button"
          onClick={onCancel}
          className="rounded p-1 text-slate-400 hover:bg-white hover:text-slate-700"
          aria-label="Close"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
      <div className="space-y-3 p-3">{children}</div>
    </motion.div>
  );
}

function InputRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-slate-500">
        {label}
      </label>
      {children}
    </div>
  );
}

const inputCls =
  "w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100";

function AddProjectForm({
  onCancel,
  onSubmit,
}: {
  onCancel: () => void;
  onSubmit: (mod: ScenarioModification) => void;
}) {
  const today = new Date().toISOString().slice(0, 10);
  const threeMonthsOut = new Date();
  threeMonthsOut.setMonth(threeMonthsOut.getMonth() + 3);
  const defaultEnd = threeMonthsOut.toISOString().slice(0, 10);

  const [name, setName] = useState("");
  const [startDate, setStartDate] = useState(today);
  const [endDate, setEndDate] = useState(defaultEnd);
  const [estHours, setEstHours] = useState(400);
  const [allocs, setAllocs] = useState<Record<string, number>>({
    developer: 0.6,
    ba: 0.3,
    pm: 0.1,
  });

  const valid = name.trim().length > 0 && estHours > 0 && endDate >= startDate;

  const handleSubmit = () => {
    if (!valid) return;
    onSubmit({
      type: "add_project",
      project: {
        name: name.trim(),
        start_date: startDate,
        end_date: endDate,
        est_hours: estHours,
        role_allocations: allocs,
      },
    });
  };

  return (
    <FormShell title="Add hypothetical project" onCancel={onCancel}>
      <InputRow label="Project name">
        <input
          className={inputCls}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Vendor Portal Rebuild"
          autoFocus
        />
      </InputRow>
      <div className="grid grid-cols-2 gap-3">
        <InputRow label="Start">
          <input
            type="date"
            className={inputCls}
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </InputRow>
        <InputRow label="End">
          <input
            type="date"
            className={inputCls}
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </InputRow>
      </div>
      <InputRow label="Estimated hours">
        <input
          type="number"
          min={0}
          step={50}
          className={inputCls}
          value={estHours}
          onChange={(e) => setEstHours(parseFloat(e.target.value) || 0)}
        />
      </InputRow>
      <InputRow label="Role allocations (% of the role's time on this project)">
        <div className="grid grid-cols-2 gap-2">
          {ROLE_OPTIONS.map((r) => (
            <div key={r.key} className="flex items-center gap-2">
              <span className="w-24 shrink-0 text-xs text-slate-600">
                {r.label}
              </span>
              <input
                type="number"
                min={0}
                max={100}
                step={5}
                className="w-16 rounded-md border border-slate-200 bg-white px-2 py-1 text-right text-xs tabular-nums"
                value={Math.round((allocs[r.key] || 0) * 100)}
                onChange={(e) => {
                  const v = (parseFloat(e.target.value) || 0) / 100;
                  setAllocs({ ...allocs, [r.key]: v });
                }}
              />
              <span className="text-xs text-slate-400">%</span>
            </div>
          ))}
        </div>
      </InputRow>
      <div className="flex items-center justify-end gap-2 pt-1">
        <Button variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
        <Button size="sm" onClick={handleSubmit} disabled={!valid}>
          <Plus className="h-3.5 w-3.5" />
          Add to scenario
        </Button>
      </div>
    </FormShell>
  );
}

function CancelProjectForm({
  projects,
  excludedIds,
  onCancel,
  onSubmit,
}: {
  projects: Project[];
  excludedIds: Set<string>;
  onCancel: () => void;
  onSubmit: (mod: ScenarioModification) => void;
}) {
  const [selected, setSelected] = useState<string>("");
  const available = projects
    .filter((p) => {
      const h = (p.health ?? "").toUpperCase();
      if (h.includes("COMPLETE") && !h.includes("INCOMPLETE")) return false;
      if (h.includes("POSTPONED")) return false;
      return !excludedIds.has(p.id);
    })
    .sort((a, b) => a.name.localeCompare(b.name));

  return (
    <FormShell title="Cancel active project" onCancel={onCancel}>
      <InputRow label="Which project?">
        <select
          className={inputCls}
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
        >
          <option value="">— select a project —</option>
          {available.map((p) => (
            <option key={p.id} value={p.id}>
              {p.id} · {p.name}
            </option>
          ))}
        </select>
      </InputRow>
      <div className="flex items-center justify-end gap-2 pt-1">
        <Button variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
        <Button
          size="sm"
          onClick={() => selected && onSubmit({ type: "cancel_project", project_id: selected })}
          disabled={!selected}
        >
          <Plus className="h-3.5 w-3.5" />
          Add to scenario
        </Button>
      </div>
    </FormShell>
  );
}

function ExcludePersonForm({
  roster,
  excludedNames,
  onCancel,
  onSubmit,
}: {
  roster: TeamMember[];
  excludedNames: Set<string>;
  onCancel: () => void;
  onSubmit: (mod: ScenarioModification) => void;
}) {
  const [selected, setSelected] = useState<string>("");
  const available = roster
    .filter((m) => m.include_in_capacity && !excludedNames.has(m.name))
    .sort((a, b) => a.name.localeCompare(b.name));

  return (
    <FormShell title="Exclude person from capacity" onCancel={onCancel}>
      <InputRow label="Which team member?">
        <select
          className={inputCls}
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
        >
          <option value="">— select a person —</option>
          {available.map((m) => (
            <option key={m.name} value={m.name}>
              {m.name} · {m.role}
            </option>
          ))}
        </select>
      </InputRow>
      <div className="flex items-center justify-end gap-2 pt-1">
        <Button variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
        <Button
          size="sm"
          onClick={() => selected && onSubmit({ type: "exclude_person", person_name: selected })}
          disabled={!selected}
        >
          <Plus className="h-3.5 w-3.5" />
          Add to scenario
        </Button>
      </div>
    </FormShell>
  );
}

function AddPersonForm({
  onCancel,
  onSubmit,
}: {
  onCancel: () => void;
  onSubmit: (mod: ScenarioModification) => void;
}) {
  const [name, setName] = useState("");
  const [roleKey, setRoleKey] = useState("developer");
  const [weekly, setWeekly] = useState(40);
  const [reserve, setReserve] = useState(0);

  const valid = name.trim().length > 0 && weekly > 0;

  return (
    <FormShell title="Add a hypothetical hire" onCancel={onCancel}>
      <InputRow label="Name">
        <input
          className={inputCls}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. New Senior Developer"
          autoFocus
        />
      </InputRow>
      <InputRow label="Role">
        <select
          className={inputCls}
          value={roleKey}
          onChange={(e) => setRoleKey(e.target.value)}
        >
          {ROLE_OPTIONS.map((r) => (
            <option key={r.key} value={r.key}>
              {r.label}
            </option>
          ))}
        </select>
      </InputRow>
      <div className="grid grid-cols-2 gap-3">
        <InputRow label="Weekly hours">
          <input
            type="number"
            min={1}
            max={60}
            step={1}
            className={inputCls}
            value={weekly}
            onChange={(e) => setWeekly(parseFloat(e.target.value) || 0)}
          />
        </InputRow>
        <InputRow label="Support reserve %">
          <input
            type="number"
            min={0}
            max={100}
            step={5}
            className={inputCls}
            value={Math.round(reserve * 100)}
            onChange={(e) => setReserve((parseFloat(e.target.value) || 0) / 100)}
          />
        </InputRow>
      </div>
      <div className="flex items-center justify-end gap-2 pt-1">
        <Button variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
        <Button
          size="sm"
          onClick={() =>
            valid &&
            onSubmit({
              type: "add_person",
              person: {
                name: name.trim(),
                role_key: roleKey,
                weekly_hrs_available: weekly,
                support_reserve_pct: reserve,
              },
            })
          }
          disabled={!valid}
        >
          <Plus className="h-3.5 w-3.5" />
          Add to scenario
        </Button>
      </div>
    </FormShell>
  );
}

// --- Stage 2 forms: shift, change allocation, resize ----------------------

function activeProjectsForSelect(projects: Project[]) {
  return projects
    .filter((p) => {
      const h = (p.health ?? "").toUpperCase();
      if (h.includes("COMPLETE") && !h.includes("INCOMPLETE")) return false;
      if (h.includes("POSTPONED")) return false;
      return true;
    })
    .sort((a, b) => a.name.localeCompare(b.name));
}

function ShiftProjectForm({
  projects,
  onCancel,
  onSubmit,
}: {
  projects: Project[];
  onCancel: () => void;
  onSubmit: (mod: ScenarioModification) => void;
}) {
  const [selected, setSelected] = useState("");
  const [newStart, setNewStart] = useState("");
  const [newEnd, setNewEnd] = useState("");
  const available = activeProjectsForSelect(projects);
  const valid = selected && (newStart || newEnd);

  return (
    <FormShell title="Shift project dates" onCancel={onCancel}>
      <InputRow label="Which project?">
        <select className={inputCls} value={selected} onChange={(e) => setSelected(e.target.value)}>
          <option value="">— select a project —</option>
          {available.map((p) => (
            <option key={p.id} value={p.id}>{p.id} · {p.name}</option>
          ))}
        </select>
      </InputRow>
      <div className="grid grid-cols-2 gap-3">
        <InputRow label="New start (blank = keep)">
          <input type="date" className={inputCls} value={newStart} onChange={(e) => setNewStart(e.target.value)} />
        </InputRow>
        <InputRow label="New end (blank = keep)">
          <input type="date" className={inputCls} value={newEnd} onChange={(e) => setNewEnd(e.target.value)} />
        </InputRow>
      </div>
      <div className="flex items-center justify-end gap-2 pt-1">
        <Button variant="ghost" size="sm" onClick={onCancel}>Cancel</Button>
        <Button size="sm" disabled={!valid} onClick={() => valid && onSubmit({ type: "shift_project", project_id: selected, new_start_date: newStart || undefined, new_end_date: newEnd || undefined })}>
          <Plus className="h-3.5 w-3.5" /> Add to scenario
        </Button>
      </div>
    </FormShell>
  );
}

function ChangeAllocationForm({
  projects,
  onCancel,
  onSubmit,
}: {
  projects: Project[];
  onCancel: () => void;
  onSubmit: (mod: ScenarioModification) => void;
}) {
  const [selected, setSelected] = useState("");
  const [roleKey, setRoleKey] = useState("developer");
  const [alloc, setAlloc] = useState(50);
  const available = activeProjectsForSelect(projects);
  const valid = selected && roleKey;

  return (
    <FormShell title="Change role allocation" onCancel={onCancel}>
      <InputRow label="Which project?">
        <select className={inputCls} value={selected} onChange={(e) => setSelected(e.target.value)}>
          <option value="">— select a project —</option>
          {available.map((p) => (
            <option key={p.id} value={p.id}>{p.id} · {p.name}</option>
          ))}
        </select>
      </InputRow>
      <div className="grid grid-cols-2 gap-3">
        <InputRow label="Role">
          <select className={inputCls} value={roleKey} onChange={(e) => setRoleKey(e.target.value)}>
            {ROLE_OPTIONS.map((r) => (<option key={r.key} value={r.key}>{r.label}</option>))}
          </select>
        </InputRow>
        <InputRow label="New allocation %">
          <input type="number" min={0} max={100} step={5} className={inputCls} value={alloc} onChange={(e) => setAlloc(parseFloat(e.target.value) || 0)} />
        </InputRow>
      </div>
      <div className="flex items-center justify-end gap-2 pt-1">
        <Button variant="ghost" size="sm" onClick={onCancel}>Cancel</Button>
        <Button size="sm" disabled={!valid} onClick={() => valid && onSubmit({ type: "change_allocation", project_id: selected, role_key: roleKey, allocation: alloc / 100 })}>
          <Plus className="h-3.5 w-3.5" /> Add to scenario
        </Button>
      </div>
    </FormShell>
  );
}

function ResizeProjectForm({
  projects,
  onCancel,
  onSubmit,
}: {
  projects: Project[];
  onCancel: () => void;
  onSubmit: (mod: ScenarioModification) => void;
}) {
  const [selected, setSelected] = useState("");
  const [hours, setHours] = useState(400);
  const available = activeProjectsForSelect(projects);
  const valid = selected && hours > 0;

  return (
    <FormShell title="Resize project scope" onCancel={onCancel}>
      <InputRow label="Which project?">
        <select className={inputCls} value={selected} onChange={(e) => setSelected(e.target.value)}>
          <option value="">— select a project —</option>
          {available.map((p) => (
            <option key={p.id} value={p.id}>{p.id} · {p.name} ({p.est_hours}h)</option>
          ))}
        </select>
      </InputRow>
      <InputRow label="New estimated hours">
        <input type="number" min={0} step={50} className={inputCls} value={hours} onChange={(e) => setHours(parseFloat(e.target.value) || 0)} />
      </InputRow>
      <div className="flex items-center justify-end gap-2 pt-1">
        <Button variant="ghost" size="sm" onClick={onCancel}>Cancel</Button>
        <Button size="sm" disabled={!valid} onClick={() => valid && onSubmit({ type: "resize_project", project_id: selected, est_hours: hours })}>
          <Plus className="h-3.5 w-3.5" /> Add to scenario
        </Button>
      </div>
    </FormShell>
  );
}
