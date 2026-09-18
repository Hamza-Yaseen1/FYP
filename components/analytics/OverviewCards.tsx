"use client";

import { Card, CardContent } from "@/components/ui/card";
import type { AnalyticsResponse } from "@/lib/api/analytics";

interface OverviewCardsProps {
  total: number;
  byPriority: AnalyticsResponse["by_priority"];
}

export default function OverviewCards({ total, byPriority }: OverviewCardsProps) {
  const items = [
    { key: "total", label: "Total Communications", value: total },
    { key: "urgent", label: "Urgent", value: byPriority.urgent },
    { key: "important", label: "Important", value: byPriority.important },
    { key: "normal", label: "Normal", value: byPriority.normal },
    { key: "low", label: "Low Priority", value: byPriority.low },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
      {items.map((item) =>
        item.key === "total" ? (
          <Card key={item.key} className="bg-primary ring-primary/30">
            <CardContent>
              <p className="triage-label text-primary-foreground/80">
                {item.label}
              </p>
              <p className="mt-2 text-3xl font-semibold tracking-tight text-primary-foreground">
                {item.value}
              </p>
            </CardContent>
          </Card>
        ) : (
          <Card key={item.key}>
            <CardContent>
              <p className="triage-label text-muted-foreground">{item.label}</p>
              <p className="mt-2 text-3xl font-semibold tracking-tight">
                {item.value}
              </p>
            </CardContent>
          </Card>
        )
      )}
    </div>
  );
}