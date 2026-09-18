import { apiFetch } from "@/lib/api";

export type AnalyticsPeriod = "day" | "week" | "month";

export interface AnalyticsResponse {
  period: AnalyticsPeriod;
  from: string;
  to: string;
  total: number;
  by_priority: {
    urgent: number;
    important: number;
    normal: number;
    low: number;
    pending: number;
  };
  by_source: Record<string, number>;
  tasks: {
    total: number;
    completed: number;
  };
  trends: {
    date: string;
    count: number;
  }[];
}

export async function analyticsFetch(
  period: AnalyticsPeriod = "week"
): Promise<AnalyticsResponse> {
  return apiFetch<AnalyticsResponse>(`/analytics?period=${period}`);
}