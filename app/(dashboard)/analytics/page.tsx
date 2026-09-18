"use client";

import { useEffect, useState } from "react";
import { BarChart3 } from "lucide-react";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import OverviewCards from "@/components/analytics/OverviewCards";
import PeriodToggle from "@/components/analytics/PeriodToggle";
import PriorityChart from "@/components/analytics/PriorityChart";
import SourceChart from "@/components/analytics/SourceChart";
import TasksProgress from "@/components/analytics/TasksProgress";
import TrendChart from "@/components/analytics/TrendChart";
import { analyticsFetch, type AnalyticsPeriod, type AnalyticsResponse } from "@/lib/api/analytics";

const PERIOD_LABELS: Record<AnalyticsPeriod, string> = {
  day: "Today",
  week: "This Week",
  month: "This Month",
};

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<AnalyticsPeriod>("week");
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    analyticsFetch(period)
      .then((result) => {
        if (!cancelled) {
          setError(null);
          setData(result);
        }
      })
      .catch(() => {
        if (!cancelled) setError("Could not load analytics data.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [period]);

  const handlePeriodChange = (next: AnalyticsPeriod) => {
    setPeriod(next);
    setLoading(true);
  };

  const hasData = data !== null && data.total > 0;

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl">
            <BarChart3 className="size-6 text-primary" aria-hidden />
            Communication Overview
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {PERIOD_LABELS[period]}
          </p>
        </div>
        <PeriodToggle value={period} onChange={handlePeriodChange} />
      </header>

      {loading ? (
        <LoadingSkeleton count={5} />
      ) : error ? (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
      ) : !hasData ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-16">
          <div className="flex size-12 items-center justify-center rounded-full bg-muted">
            <BarChart3 className="size-5 text-muted-foreground" />
          </div>
          <h3 className="mt-4 text-sm font-semibold">No data yet</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {PERIOD_LABELS[period]} analytics will appear here once messages arrive.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          <section aria-label="Communication overview">
            <h2 className="triage-label mb-3 text-muted-foreground">Overview</h2>
            <OverviewCards total={data.total} byPriority={data.by_priority} />
          </section>
          <section aria-label="Communication charts">
            <h2 className="triage-label mb-3 text-muted-foreground">Channels</h2>
            <div className="grid gap-4 lg:grid-cols-2">
              <SourceChart bySource={data.by_source} />
              <TasksProgress total={data.tasks.total} completed={data.tasks.completed} />
              <div className="lg:col-span-2">
                <PriorityChart byPriority={data.by_priority} />
              </div>
              <div className="lg:col-span-2">
                <TrendChart trends={data.trends} />
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}