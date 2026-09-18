"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const TOOLTIP_STYLE = {
  background: "var(--card)",
  border: "1px solid var(--border)",
  borderRadius: "0.625rem",
  color: "var(--card-foreground)",
  fontSize: "12px",
} as const;

interface TasksProgressProps {
  total: number;
  completed: number;
}

export default function TasksProgress({ total, completed }: TasksProgressProps) {
  if (total === 0) {
    return (
      <Card className="pastel-border ring-0">
        <CardHeader>
          <CardTitle>Tasks Completed</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No tasks extracted yet.</p>
        </CardContent>
      </Card>
    );
  }

  const remaining = Math.max(total - completed, 0);
  const data = [
    { name: "Completed", value: completed },
    { name: "Remaining", value: remaining },
  ];

  return (
    <Card className="pastel-border ring-0">
      <CardHeader>
        <CardTitle>Tasks Completed</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center gap-6">
        <ResponsiveContainer width="45%" height={180}>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={52}
              outerRadius={72}
              paddingAngle={2}
              stroke="none"
            >
              <Cell fill="var(--chart-1)" />
              <Cell fill="var(--chart-5)" />
            </Pie>
            <Tooltip contentStyle={TOOLTIP_STYLE} />
          </PieChart>
        </ResponsiveContainer>
        <div>
          <p className="text-3xl font-semibold tracking-tight">
            {completed}
            <span className="text-muted-foreground">/{total}</span>
          </p>
          <p className="triage-label mt-1 text-muted-foreground">completed</p>
        </div>
      </CardContent>
    </Card>
  );
}