import { useParams } from "react-router-dom";
import { ProjectHero } from "@/components/project/ProjectHero";
import { ProjectKpiStrip } from "@/components/project/ProjectKpiStrip";
import { RoleDemandCard } from "@/components/project/RoleDemandCard";
import { MilestonesPanel } from "@/components/project/MilestonesPanel";
import { CommentsPanel } from "@/components/project/CommentsPanel";
import { useProject } from "@/hooks/usePortfolio";
import { useProjectDemand } from "@/hooks/useProjectDemand";
import { useMilestones } from "@/hooks/useMilestones";
import { useComments } from "@/hooks/useComments";

export function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();

  const project = useProject(projectId);
  const demand = useProjectDemand(projectId);
  const milestones = useMilestones(projectId);
  const comments = useComments(projectId);

  if (project.isLoading) {
    return <LoadingState />;
  }
  if (project.isError || !project.data) {
    return (
      <div className="p-8">
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-800">
          Project not found: {projectId}
        </div>
      </div>
    );
  }

  const p = project.data;

  return (
    <div className="space-y-6 p-8">
      <ProjectHero project={p} />

      <ProjectKpiStrip
        project={p}
        durationWeeks={demand.data?.duration_weeks ?? p.duration_weeks ?? 0}
      />

      {demand.data && <RoleDemandCard demand={demand.data} />}

      <div className="grid gap-6 lg:grid-cols-2">
        {milestones.data && projectId && (
          <MilestonesPanel projectId={projectId} milestones={milestones.data} />
        )}
        {comments.data && projectId && (
          <CommentsPanel projectId={projectId} comments={comments.data} />
        )}
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="p-8">
      <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-500">
        Loading project…
      </div>
    </div>
  );
}
