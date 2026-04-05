import { useEffect, useMemo, useState } from "react";
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
import { useRoster } from "@/hooks/useRoster";
import { useUpsertAssignment } from "@/hooks/useAssignments";
import type { Assignment } from "@/types/assignment";
import type { Project } from "@/types/project";

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
  /** Existing assignments for this project. Used to filter out people
   *  already assigned to the chosen role at 100%. */
  existing: Assignment[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AssignPersonDialog({
  project,
  existing,
  open,
  onOpenChange,
}: Props) {
  const roster = useRoster();
  const mutation = useUpsertAssignment();

  // Default role = first role with non-zero allocation, else developer
  const defaultRole = useMemo(() => {
    for (const key of ROLE_KEYS) {
      if ((project.role_allocations?.[key] ?? 0) > 0) return key;
    }
    return "developer";
  }, [project.role_allocations]);

  const [roleKey, setRoleKey] = useState<string>(defaultRole);
  const [personName, setPersonName] = useState<string>("");
  const [allocationPct, setAllocationPct] = useState<string>("50");

  useEffect(() => {
    if (open) {
      setRoleKey(defaultRole);
      setPersonName("");
      setAllocationPct("50");
      mutation.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, defaultRole]);

  // People eligible for the selected role (filter roster by role_key)
  const eligible = useMemo(() => {
    const all = roster.data ?? [];
    const alreadyAssigned = new Set(
      existing.filter((a) => a.role_key === roleKey).map((a) => a.person_name),
    );
    return all
      .filter((m) => m.role_key === roleKey)
      .filter((m) => !alreadyAssigned.has(m.name))
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [roster.data, roleKey, existing]);

  // When the role changes, reset the person to the first eligible option
  useEffect(() => {
    if (eligible.length > 0) {
      setPersonName(eligible[0].name);
    } else {
      setPersonName("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roleKey, eligible.length]);

  const handleSave = async () => {
    if (!personName) return;
    const pct = Math.max(
      0,
      Math.min(1, (Number.parseFloat(allocationPct) || 0) / 100),
    );
    try {
      await mutation.mutateAsync({
        project_id: project.id,
        person_name: personName,
        role_key: roleKey,
        allocation_pct: pct,
      });
      onOpenChange(false);
    } catch {
      /* error surfaces via mutation.error */
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Assign person</DialogTitle>
          <DialogDescription>
            Assign a team member to <span className="font-mono">{project.id}</span>{" "}
            at a specific allocation.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-2">
          <Field label="Role">
            <select
              value={roleKey}
              onChange={(e) => setRoleKey(e.target.value)}
              className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
            >
              {ROLE_KEYS.map((key) => (
                <option key={key} value={key}>
                  {ROLE_LABEL[key]}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Person">
            {roster.isLoading ? (
              <div className="text-xs text-slate-500">Loading roster…</div>
            ) : eligible.length === 0 ? (
              <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500">
                No {ROLE_LABEL[roleKey].toLowerCase()}s available. Either the
                project already has everyone assigned, or nobody in the roster
                has that role.
              </div>
            ) : (
              <select
                value={personName}
                onChange={(e) => setPersonName(e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
              >
                {eligible.map((m) => (
                  <option key={m.name} value={m.name}>
                    {m.name}
                  </option>
                ))}
              </select>
            )}
          </Field>

          <Field label="Allocation">
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={5}
                max={100}
                step={5}
                value={Number.parseFloat(allocationPct) || 0}
                onChange={(e) => setAllocationPct(e.target.value)}
                className="flex-1 accent-navy-900"
              />
              <div className="relative w-20">
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={allocationPct}
                  onChange={(e) => setAllocationPct(e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-white py-1.5 pl-2 pr-7 text-right text-sm tabular-nums focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
                />
                <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-xs text-slate-400">
                  %
                </span>
              </div>
            </div>
            <div className="mt-1 text-[11px] text-slate-500">
              Fraction of this person's capacity consumed by this project-role.
            </div>
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
            disabled={mutation.isPending || !personName}
          >
            {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Assign
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
