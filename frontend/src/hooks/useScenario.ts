import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  ScenarioEvaluateRequest,
  ScenarioEvaluateResponse,
  SchedulePortfolioRequest,
  SchedulePortfolioResponse,
} from "@/types/scenario";

/**
 * POST /scenarios/evaluate — runs a what-if scenario and returns the
 * baseline + modified sides so the UI can render a before/after view.
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

/**
 * POST /scenarios/schedule-portfolio — runs the greedy capacity-aware
 * scheduler on all plannable projects and returns suggested start/end
 * dates, bottleneck roles, and feasibility info.
 */
export function useSchedulePortfolio() {
  return useMutation({
    mutationFn: async (
      payload?: SchedulePortfolioRequest,
    ): Promise<SchedulePortfolioResponse> => {
      const { data } = await api.post<SchedulePortfolioResponse>(
        "/scenarios/schedule-portfolio",
        payload ?? {},
      );
      return data;
    },
  });
}
