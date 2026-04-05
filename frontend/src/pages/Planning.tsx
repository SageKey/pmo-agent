import { useEffect, useState } from "react";
import { PlayCircle, Sparkles } from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { Button } from "@/components/ui/button";
import { ScenarioBuilder } from "@/components/planning/ScenarioBuilder";
import { ScenarioComparison } from "@/components/planning/ScenarioComparison";
import { usePortfolio } from "@/hooks/usePortfolio";
import { useRoster } from "@/hooks/useRoster";
import { useEvaluateScenario } from "@/hooks/useScenario";
import type { ScenarioModification } from "@/types/scenario";

export function Planning() {
  const [modifications, setModifications] = useState<ScenarioModification[]>([]);
  const portfolio = usePortfolio();
  const roster = useRoster();
  const evaluate = useEvaluateScenario();

  // Auto-evaluate whenever the modification list changes. Debounced via
  // the fact that useMutation collapses rapid calls, and the backend is
  // fast enough (<100ms per evaluate) that this feels live.
  useEffect(() => {
    evaluate.mutate({ modifications });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(modifications)]);

  const hasMods = modifications.length > 0;

  return (
    <>
      <TopBar
        title="Planning"
        subtitle="What-if scenarios — see the impact before you commit."
      />
      <div className="space-y-6 p-8">
        {/* Intro card */}
        <div className="rounded-xl border border-navy-200 bg-gradient-to-r from-navy-50 to-white px-6 py-4 ring-1 ring-inset ring-navy-100">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 rounded-md bg-white p-2 text-navy-700 ring-1 ring-inset ring-navy-200">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-semibold text-navy-900">
                Scenario planning
              </div>
              <p className="mt-0.5 text-xs text-slate-600">
                Stack modifications on the left to explore "what if we take on
                this project?", "what if we lose a resource?", or "what if we
                hire another developer?". The engine runs live — no saves, no
                side effects, nothing written to the database.
              </p>
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
          {/* Left: builder */}
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

          {/* Right: comparison */}
          <div>
            <ScenarioComparison
              result={evaluate.data}
              isPending={evaluate.isPending}
              hasModifications={hasMods}
            />
          </div>
        </div>
      </div>
    </>
  );
}
