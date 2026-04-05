import { useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowLeft, Pencil } from "lucide-react";
import type { Project } from "@/types/project";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { HealthBadge } from "@/components/portfolio/HealthBadge";
import { PriorityPill } from "@/components/portfolio/PriorityPill";
import { EditProjectDialog } from "@/components/project/EditProjectDialog";
import { avatarTone, initials, pct, relativeDate, shortDate } from "@/lib/format";
import { cn } from "@/lib/cn";

const RELATIVE_TONE: Record<string, string> = {
  past: "text-red-600",
  soon: "text-amber-600",
  future: "text-slate-500",
  none: "text-slate-400",
};

export function ProjectHero({ project }: { project: Project }) {
  const rel = relativeDate(project.end_date);
  const completion = Math.min(Math.max(project.pct_complete, 0), 1);
  const [editOpen, setEditOpen] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
    >
      <Card className="ring-1 ring-inset ring-slate-200">
        <div className="p-6">
          <div className="flex items-center justify-between">
            <Link
              to="/portfolio"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-900"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Portfolio
            </Link>
            <Button variant="outline" size="sm" onClick={() => setEditOpen(true)}>
              <Pencil className="h-3.5 w-3.5" />
              Edit
            </Button>
          </div>

          <div className="mt-3 flex items-start gap-5">
            <div
              className={cn(
                "flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl text-lg font-semibold",
                avatarTone(project.pm),
              )}
              title={project.pm ?? ""}
            >
              {initials(project.pm)}
            </div>

            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 font-mono text-xs font-medium text-slate-600">
                  {project.id}
                </span>
                <PriorityPill priority={project.priority} />
                <HealthBadge health={project.health} />
                {project.portfolio && (
                  <span className="text-xs text-slate-500">· {project.portfolio}</span>
                )}
              </div>
              <h1 className="mt-1.5 text-2xl font-semibold tracking-tight text-slate-900">
                {project.name}
              </h1>
              <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
                <span>
                  PM:{" "}
                  <span className="font-medium text-slate-700">
                    {project.pm ?? "—"}
                  </span>
                </span>
                {project.sponsor && (
                  <span>
                    Sponsor:{" "}
                    <span className="font-medium text-slate-700">{project.sponsor}</span>
                  </span>
                )}
                <span>
                  {shortDate(project.start_date)} → {shortDate(project.end_date)}
                </span>
                <span className={RELATIVE_TONE[rel.tone]}>{rel.label}</span>
              </div>
            </div>
          </div>

          {/* Progress bar */}
          <div className="mt-5">
            <div className="mb-1.5 flex items-center justify-between text-xs">
              <span className="font-medium text-slate-600">Progress</span>
              <span className="font-semibold tabular-nums text-slate-900">
                {pct(completion)}
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${completion * 100}%` }}
                transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
                className={cn(
                  "h-full rounded-full",
                  completion >= 1
                    ? "bg-emerald-500"
                    : completion >= 0.5
                      ? "bg-navy-500"
                      : "bg-slate-400",
                )}
              />
            </div>
          </div>
        </div>
      </Card>
      <EditProjectDialog
        project={project}
        open={editOpen}
        onOpenChange={setEditOpen}
      />
    </motion.div>
  );
}
