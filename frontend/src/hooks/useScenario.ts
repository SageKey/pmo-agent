import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  ScenarioEvaluateRequest,
  ScenarioEvaluateResponse,
} from "@/types/scenario";

/**
 * POST /scenarios/evaluate — runs a what-if scenario and returns the
 * baseline + modified sides so the UI can render a before/after view.
 *
 * Uses useMutation rather than useQuery because a scenario evaluation
 * is an explicit user action, not a passively-refetched state. Each
 * click of "Evaluate" creates a fresh call.
 */
export function useEvaluateScenario() {
  return useMutation({
    mutationFn: async (
      payload: ScenarioEvaluateRequest,
    ): Promise<ScenarioEvaluateResponse> => {
      const { data } = await api.post<ScenarioEvaluateResponse>(
        "/scenarios/evaluate",
        payload,
      );
      return data;
    },
  });
}
