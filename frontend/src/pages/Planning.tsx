import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { PlayCircle, Sparkles, CalendarClock, FlaskConical, HelpCircle, ChevronDown } from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { Button } from "@/components/ui/button";
import { ScenarioBuilder } from "@/components/planning/ScenarioBuilder";
import { ScenarioComparison } from "@/components/planning/ScenarioComparison";
import { ScheduleView } from "@/components/planning/ScheduleView";
import { usePortfolio } from "@/hooks/usePortfolio";
import { useRoster } from "@/hooks/useRoster";
import { useEvaluateScenario } from "@/hooks/useScenario";
import { cn } from "@/lib/cn";
import type { ScenarioModification } from "@/types/scenario";

type Tab = "schedule" | "scenario";

export function Planning() {
  const [tab, setTab] = useState<Tab>("schedule");
  const [modifications, setModifications] = useState<ScenarioModification[]>([]);
  const portfolio = usePortfolio();
  const roster = useRoster();
  const evaluate = useEvaluateScenario();

  useEffect(() => {
    if (tab === "scenario") {
      evaluate.mutate({ modifications });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(modifications), tab]);

  const hasMods = modifications.length > 0;

  return (
    <>
      <TopBar
        title="Planning"
        subtitle="Capacity-driven scheduling and what-if analysis."
      />
      <div className="space-y-6 p-8">
        {/* Tabs */}
        <div className="flex items-center gap-1 rounded-lg bg-slate-100 p-1">
          <TabButton
            active={tab === "schedule"}
            onClick={() => setTab("schedule")}
            icon={<CalendarClock className="h-4 w-4" />}
            label="Auto-Schedule"
            badge={hasMods ? modifications.length : undefined}
          />
          <TabButton
            active={tab === "scenario"}
            onClick={() => setTab("scenario")}
            icon={<FlaskConical className="h-4 w-4" />}
            label="What-If Scenario"
          />
        </div>

        {/* Collapsible workflow guide */}
        <WorkflowGuide />

        {/* Tab content */}
        {tab === "schedule" && <ScheduleView modifications={modifications} />}

        {tab === "scenario" && (
          <>
            {/* Intro */}
            <div className="rounded-xl border border-navy-200 bg-gradient-to-r from-navy-50 to-white px-6 py-4 ring-1 ring-inset ring-navy-100">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 rounded-md bg-white p-2 text-navy-700 ring-1 ring-inset ring-navy-200">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-navy-900">
                    What-if scenario
                  </div>
                  <p className="mt-0.5 text-xs text-slate-600">
                    Stack modifications to explore "what if we take on this
                    project?", "what if we lose a resource?", or "what if we
                    hire another developer?". Nothing is saved — pure
                    exploration.
                  </p>
                </div>
              </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
              <div className="space-y-4">
                <ScenarioBuilder
                  modifications={modifications}
                  onChange={setModifications}
                  projects={portfolio.data ?? []}
                  roster={roster.data ?? []}
                />
                {hasMods && (
                  <Button
                    variant="default"
                    className="w-full"
                    onClick={() => evaluate.mutate({ modifications })}
                    disabled={evaluate.isPending}
                  >
                    <PlayCircle className="h-4 w-4" />
                    {evaluate.isPending ? "Evaluating…" : "Re-run scenario"}
                  </Button>
                )}
              </div>
              <div>
                <ScenarioComparison
                  result={evaluate.data}
                  isPending={evaluate.isPending}
                  hasModifications={hasMods}
                />
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
}

function TabButton({
  active,
  onClick,
  icon,
  label,
  badge,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  badge?: number;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "relative flex flex-1 items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-all",
        active
          ? "bg-white text-navy-900 shadow-sm"
          : "text-slate-500 hover:text-slate-800",
      )}
    >
      {icon}
      {label}
      {badge != null && badge > 0 && (
        <span className="rounded-full bg-navy-700 px-1.5 py-0.5 text-[10px] font-bold tabular-nums text-white">
          {badge}
        </span>
      )}
      {active && (
        <motion.div
          layoutId="planning-tab-indicator"
          className="absolute inset-0 rounded-md bg-white shadow-sm"
          style={{ zIndex: -1 }}
          transition={{ type: "spring", duration: 0.4, bounce: 0.15 }}
        />
      )}
    </button>
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
            <div className="font-semibold text-slate-800 mb-1">Step 1 — Check the baseline</div>
            <p>
              The <strong>Auto-Schedule</strong> tab runs automatically. It shows which
              plannable projects can start now, which are queued behind capacity
              constraints, and which roles are the bottleneck.
            </p>
          </div>
          <div>
            <div className="font-semibold text-slate-800 mb-1">Step 2 — Explore what-if scenarios</div>
            <p>
              Switch to the <strong>What-If</strong> tab and stack modifications: add a
              project, exclude a person, hire someone, shift dates, resize scope,
              or change a role allocation. The right panel shows instant
              before/after utilization impact per role.
            </p>
          </div>
          <div>
            <div className="font-semibold text-slate-800 mb-1">Step 3 — See the scheduling impact</div>
            <p>
              Switch back to <strong>Auto-Schedule</strong>. Your modifications carry over
              (badge shows the count). The scheduler re-runs against the modified
              data so you can see how your changes affect project placement and timelines.
            </p>
          </div>
          <div>
            <div className="font-semibold text-slate-800 mb-1">Step 4 — Iterate</div>
            <p>
              Add, remove, or swap modifications. Both tabs re-compute instantly.
              Nothing is saved — scenarios are ephemeral exploration, not database writes.
            </p>
          </div>
          <div className="rounded-md bg-slate-50 px-4 py-3 text-xs text-slate-500 space-y-1">
            <div><strong>Priority drives placement order.</strong> Highest goes first, then High, Medium, Low. Larger projects go first within a tier.</div>
            <div><strong>Bottleneck role</strong> = the role that prevented an earlier start. If the same role blocks multiple projects, that's a hiring or reallocation signal.</div>
            <div><strong>Utilization ceiling</strong> defaults to the admin threshold (Settings page). Lower it to build in headroom.</div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
