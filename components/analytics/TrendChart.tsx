"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AnalyticsResponse } from "@/lib/api/analytics";

const TOOLTIP_STYLE = {
  background: "var(--card)",
  border: "1px solid var(--border)",
  borderRadius: "0.625rem",
  color: "var(--card-foreground)",
  fontSize: "12px",
} as const;

interface TrendChartProps {
  trends: AnalyticsResponse["trends"];
}

const formatTick = (value: string) =>
  value.includes("T") ? value.slice(11, 16) : value.slice(5);

export default function TrendChart({ trends }: TrendChartProps) {
  if (trends.length === 0) return null;

  return (
    <Card className="pastel-border ring-0">
      <CardHeader>
        <CardTitle>Attention trends</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart
            data={trends}
            margin={{ top: 8, right: 8, left: -20, bottom: 0 }}
          >
            <defs>
              <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--signal)" stopOpacity={0.35} />
                <stop offset="95%" stopColor="var(--signal)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="var(--border)" />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              fontSize={11}
              fill="var(--muted-foreground)"
              tickFormatter={formatTick}
            />
            <YAxis
              allowDecimals={false}
              tickLine={false}
              axisLine={false}
              fontSize={12}
              fill="var(--muted-foreground)"
            />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Area
              type="monotone"
              dataKey="count"
              stroke="var(--signal)"
              strokeWidth={2}
              fill="url(#trendFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}