"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AnalyticsResponse } from "@/lib/api/analytics";

const SOURCE_COLORS: Record<string, string> = {
  whatsapp: "var(--chart-1)",
  gmail: "var(--chart-2)",
};

const TOOLTIP_STYLE = {
  background: "var(--card)",
  border: "1px solid var(--border)",
  borderRadius: "0.625rem",
  color: "var(--card-foreground)",
  fontSize: "12px",
} as const;

interface SourceChartProps {
  bySource: AnalyticsResponse["by_source"];
}

export default function SourceChart({ bySource }: SourceChartProps) {
  const data = Object.entries(bySource).map(([key, count]) => ({
    key,
    name: key.charAt(0).toUpperCase() + key.slice(1),
    count,
  }));

  if (data.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Communications by source</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--border)" />
            <XAxis
              dataKey="name"
              tickLine={false}
              axisLine={false}
              fontSize={12}
              fill="var(--muted-foreground)"
            />
            <YAxis
              allowDecimals={false}
              tickLine={false}
              axisLine={false}
              fontSize={12}
              fill="var(--muted-foreground)"
            />
            <Tooltip cursor={{ fill: "var(--accent)" }} contentStyle={TOOLTIP_STYLE} />
            <Bar dataKey="count" radius={[6, 6, 0, 0]}>
              {data.map((entry) => (
                <Cell key={entry.key} fill={SOURCE_COLORS[entry.key] ?? "var(--chart-5)"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}