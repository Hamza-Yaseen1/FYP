"use client";

import { useState } from "react";
import HealthBadge from "@/components/HealthBadge";
import MessageList from "@/components/MessageList";
import SimulateMessage from "@/components/SimulateMessage";

export default function DashboardPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="p-6 space-y-8">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Good morning, Hamza 👋
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            You have{" "}
            <span className="font-medium text-foreground">3 things</span>{" "}
            needing attention.
          </p>
        </div>
        <HealthBadge />
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border bg-card p-5">
          <div className="flex items-center gap-3">
            <span className="size-2.5 rounded-full bg-red-500" />
            <span className="text-sm text-muted-foreground">Urgent</span>
          </div>
          <p className="mt-3 text-3xl font-bold">3</p>
        </div>
        <div className="rounded-xl border bg-card p-5">
          <div className="flex items-center gap-3">
            <span className="size-2.5 rounded-full bg-yellow-500" />
            <span className="text-sm text-muted-foreground">Important</span>
          </div>
          <p className="mt-3 text-3xl font-bold">4</p>
        </div>
        <div className="rounded-xl border bg-card p-5">
          <div className="flex items-center gap-3">
            <span className="size-2.5 rounded-full bg-emerald-500" />
            <span className="text-sm text-muted-foreground">Normal</span>
          </div>
          <p className="mt-3 text-3xl font-bold">12</p>
        </div>
      </div>

      {/* Needs attention */}
      <div>
        <h2 className="mb-4 text-lg font-semibold">Needs Your Attention</h2>
        <div className="space-y-3">
          {[
            { color: "bg-red-500", title: "FYP presentation", source: "WhatsApp", sender: "Ali", time: "2m ago", deadline: "Tonight" },
            { color: "bg-red-500", title: "Submit report before 5 PM", source: "Gmail", sender: "Teacher", time: "18m ago", deadline: "Today, 5:00 PM" },
            { color: "bg-yellow-500", title: "Review project requirements", source: "Gmail", sender: "Supervisor", time: "1h ago", deadline: "Tomorrow" },
          ].map((item, i) => (
            <div
              key={i}
              className="flex items-center justify-between rounded-xl border bg-card p-4"
            >
              <div className="flex items-center gap-4">
                <span className={`size-2.5 shrink-0 rounded-full ${item.color}`} />
                <div>
                  <p className="text-sm font-medium">{item.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.source} · {item.sender} · {item.time}
                  </p>
                </div>
              </div>
              <span className="text-xs text-muted-foreground hidden sm:inline">
                Deadline: {item.deadline}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Recent messages */}
      <div>
        <h2 className="mb-4 text-lg font-semibold">Recent Messages</h2>
        <MessageList refreshKey={refreshKey} />
      </div>

      {/* Simulate message */}
      <div className="rounded-xl border bg-card p-5">
        <h2 className="mb-3 text-lg font-semibold">Simulate Message</h2>
        <SimulateMessage
          onSent={() => setRefreshKey((k) => k + 1)}
        />
      </div>
    </div>
  );
}
