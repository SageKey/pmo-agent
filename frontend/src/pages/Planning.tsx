import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  HelpCircle,
  ChevronDown,
  Sparkles,
} from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { ScenarioBuilder } from "@/components/planning/ScenarioBuilder";
import { ScheduleView } from "@/components/planning/ScheduleView";
import { ScenarioComparison } from "@/components/planning/ScenarioComparison";
import { usePortfolio } from "@/hooks/usePortfolio";
import { useRoster } from "@/hooks/useRoster";
import { useEvaluateScenario } from "@/hooks/useScenario";
import { cn } from "@/lib/cn";
import type { ScenarioModification } from "@/types/scenario";

export function Planning() {
  const [modifications, setModifications] = useState<ScenarioModification[]>([]);
  const [showUtilDetail, setShowUtilDetail] = useState(false);
  const portfolio = usePortfolio();
  const roster = useRoster();
  const evaluate = useEvaluateScenario();

  const hasMods = modifications.length > 0;

  // Evaluate utilization impact whenever modifications change
  useEffect(() => {
    if (hasMods) {
      evaluate.mutate({ modifications });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(modifications)]);

  return (
    <>
      <TopBar
        title="Planning"
        subtitle="Capacity-driven scheduling and what-if analysis."
      />
      <div className="space-y-6 p-8">
        {/* Workflow guide */}
        <WorkflowGuide />

        {/* Main layout: builder on left, schedule + impact on right */}
        <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
          {/* Left: modification builder */}
          <div className="space-y-4">
            <ScenarioBuilder
              modifications={modifications}
              onChange={setModifications}
              projects={portfolio.data ?? []}
              roster={roster.data ?? []}
            />

            {/* Utilization detail — collapsible, below the builder */}
            {hasMods && (
              <div className="rounded-xl border border-slate-200 bg-white">
                <button
                  type="button"
                  onClick={() => setShowUtilDetail(!showUtilDetail)}
                  className="flex w-full items-center gap-2 px-5 py-3 text-left text-sm font-medium text-slate-700 hover:text-navy-800 transition-colors"
                >
                  <Sparkles className="h-4 w-4 text-slate-400" />
                  Utilization impact detail
                  <ChevronDown
                    className={cn(
                      "ml-auto h-4 w-4 text-slate-400 transition-transform",
                      showUtilDetail && "rotate-180",
                    )}
                  />
                </button>
                {showUtilDetail && (
                  <div className="border-t border-slate-100 p-4">
                    <ScenarioComparison
                      result={evaluate.data}
                      isPending={evaluate.isPending}
                      hasModifications={hasMods}
                    />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right: schedule results (in-flight + plannable + summary) */}
          <div>
            <ScheduleView modifications={modifications} />
          </div>
        </div>
      </div>
    </>
  );
}

function WorkflowGuide() {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-xl border border-slate-200 bg-white">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-5 py-3 text-left text-sm font-medium text-slate-700 hover:text-navy-800 transition-colors"
      >
        <HelpCircle className="h-4 w-4 text-slate-400" />
        How to use the Planning module
        <ChevronDown
          className={cn(
            "ml-auto h-4 w-4 text-slate-400 transition-transform",
            open && "rotate-180",
          )}
        />
      </button>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="border-t border-slate-100 px-5 py-4 text-sm text-slate-600 space-y-4"
        >
          <div>
            <div className="font-semibold text-slate-800 mb-1">1. Review the baseline schedule</div>
            <p>
              The right panel shows your current capacity picture: <strong>in-flight
              projects</strong> consuming capacity at the top, then <strong>plannable
              projects</strong> with suggested start dates based on when roles have room.
              Bottleneck roles are flagged so you know what's blocking placement.
            </p>
          </div>
          <div>
            <div className="font-semibold text-slate-800 mb-1">2. Explore modifications</div>
            <p>
              Use the builder on the left to stack what-if changes: add a project,
              exclude a person, hire someone, shift dates, resize scope, or change
              allocations. The schedule re-computes live — no saves, no side effects.
            </p>
          </div>
          <div>
            <div className="font-semibold text-slate-800 mb-1">3. Check utilization detail</div>
            <p>
              When modifications are active, expand <strong>Utilization impact
              detail</strong> below the builder to see before/after utilization per
              role with delta arrows and status-change highlighting.
            </p>
          </div>
          <div>
            <div className="font-semibold text-slate-800 mb-1">4. Iterate</div>
            <p>
              Add, remove, or swap modifications. Both the schedule and the
              utilization detail re-compute instantly. Clear all to return to the
              baseline view.
            </p>
          </div>
          <div className="rounded-md bg-slate-50 px-4 py-3 text-xs text-slate-500 space-y-1">
            <div><strong>Priority drives placement.</strong> Highest-priority projects get first pick of calendar space.</div>
            <div><strong>In-flight projects are fixed.</strong> They consume capacity but their dates aren't moved by the scheduler.</div>
            <div><strong>Bottleneck role</strong> = the role preventing an earlier start. Recurring bottlenecks signal a hiring need.</div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
