"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AnalyticsResponse } from "@/lib/api/analytics";

const TOOLTIP_STYLE = {
  background: "var(--card)",
  border: "1px solid var(--border)",
  borderRadius: "0.625rem",
  color: "var(--card-foreground)",
  fontSize: "12px",
} as const;

const PRIORITY_ORDER: {
  key: keyof AnalyticsResponse["by_priority"];
  label: string;
  color: string;
}[] = [
  { key: "urgent", label: "Urgent", color: "var(--ember)" },
  { key: "important", label: "Important", color: "var(--signal)" },
  { key: "normal", label: "Normal", color: "var(--cool)" },
  { key: "low", label: "Low", color: "var(--chart-4)" },
  { key: "pending", label: "Pending", color: "var(--chart-5)" },
];

interface PriorityChartProps {
  byPriority: AnalyticsResponse["by_priority"];
}

export default function PriorityChart({ byPriority }: PriorityChartProps) {
  const data = PRIORITY_ORDER.map(({ key, label, color }) => ({
    name: label,
    value: byPriority[key],
    color,
  })).filter((entry) => entry.value > 0);

  if (data.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Priority distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={55}
              outerRadius={80}
              paddingAngle={2}
              stroke="none"
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend
              wrapperStyle={{
                color: "var(--card-foreground)",
                fontSize: "12px",
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}