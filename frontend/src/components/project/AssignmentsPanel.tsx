import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Plus, Trash2, Users, UserPlus } from "lucide-react";
import { Link } from "react-router-dom";
import type { Assignment } from "@/types/assignment";
import type { Project } from "@/types/project";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AssignPersonDialog } from "./AssignPersonDialog";
import { useDeleteAssignment } from "@/hooks/useAssignments";
import { avatarTone, initials, pct } from "@/lib/format";
import { cn } from "@/lib/cn";

const ROLE_LABEL: Record<string, string> = {
  pm: "Project Manager",
  ba: "Business Analyst",
  functional: "Functional",
  technical: "Technical",
  developer: "Developer",
  infrastructure: "Infrastructure",
  dba: "DBA",
  erp: "ERP",
};

const ROLE_ORDER = [
  "pm",
  "ba",
  "functional",
  "technical",
  "developer",
  "infrastructure",
  "dba",
  "erp",
];

export function AssignmentsPanel({
  project,
  assignments,
}: {
  project: Project;
  assignments: Assignment[];
}) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const deleteMutation = useDeleteAssignment();

  const grouped = useMemo(() => {
    const byRole = new Map<string, Assignment[]>();
    for (const a of assignments) {
      if (!byRole.has(a.role_key)) byRole.set(a.role_key, []);
      byRole.get(a.role_key)!.push(a);
    }
    for (const arr of byRole.values()) {
      arr.sort((a, b) => b.allocation_pct - a.allocation_pct);
    }
    return ROLE_ORDER.filter((r) => byRole.has(r)).map((r) => ({
      role_key: r,
      items: byRole.get(r)!,
    }));
  }, [assignments]);

  const handleDelete = (a: Assignment) => {
    if (confirm(`Unassign ${a.person_name} from this project?`)) {
      deleteMutation.mutate({
        project_id: a.project_id,
        person_name: a.person_name,
        role_key: a.role_key,
      });
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>People assigned</CardTitle>
          <div className="flex items-center gap-3">
            {assignments.length > 0 && (
              <span className="text-xs tabular-nums text-slate-500">
                {assignments.length}{" "}
                {assignments.length === 1 ? "person" : "people"}
              </span>
            )}
            <Button size="sm" variant="outline" onClick={() => setDialogOpen(true)}>
              <Plus className="h-3.5 w-3.5" />
              Assign
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {assignments.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-10 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
              <UserPlus className="h-6 w-6" />
            </div>
            <div className="text-sm font-semibold text-slate-700">
              No one assigned yet
            </div>
            <div className="max-w-md text-xs text-slate-500">
              Until you assign specific people, capacity falls back to even-splitting
              role demand across everyone in that role. Assigning makes the numbers
              accurate.
            </div>
          </div>
        ) : (
          <div className="space-y-5">
            {grouped.map(({ role_key, items }) => (
              <div key={role_key}>
                <div className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  <Users className="h-3 w-3" />
                  {ROLE_LABEL[role_key] ?? role_key}
                  <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold tabular-nums text-slate-600">
                    {items.length}
                  </span>
                </div>
                <ul className="divide-y divide-slate-100 overflow-hidden rounded-lg border border-slate-200">
                  {items.map((a, i) => (
                    <motion.li
                      key={`${a.person_name}-${a.role_key}`}
                      initial={{ opacity: 0, y: 3 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.25, delay: i * 0.03 }}
                      className="group flex items-center gap-3 px-3 py-2.5"
                    >
                      <div
                        className={cn(
                          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold",
                          avatarTone(a.person_name),
                        )}
                      >
                        {initials(a.person_name)}
                      </div>
                      <Link
                        to={`/roster`}
                        className="min-w-0 flex-1 truncate text-sm font-medium text-slate-900 hover:text-navy-700"
                      >
                        {a.person_name}
                      </Link>
                      <div className="shrink-0 text-xs tabular-nums text-slate-600">
                        {pct(a.allocation_pct)} allocation
                      </div>
                      <button
                        onClick={() => handleDelete(a)}
                        disabled={deleteMutation.isPending}
                        className="rounded p-1 text-slate-300 opacity-0 transition-all hover:bg-red-50 hover:text-red-600 group-hover:opacity-100"
                        title="Unassign"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </motion.li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      <AssignPersonDialog
        project={project}
        existing={assignments}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
      />
    </Card>
  );
}
