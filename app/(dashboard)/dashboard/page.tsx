"use client";

import { useEffect, useState } from "react";
import HealthBadge from "@/components/HealthBadge";
import MessageList from "@/components/MessageList";
import NeedsAttentionSection from "@/components/NeedsAttentionSection";
import SimulateMessage from "@/components/SimulateMessage";

interface Task {
  id: string;
  description: string;
  deadline: string | null;
  priority_indicator: string | null;
  status: string;
  source_message_preview: string;
  created_at: string;
}

export default function DashboardPage() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [tasks, setTasks] = useState<Task[]>([]);

  useEffect(() => {
    let cancelled = false;
    fetch("http://localhost:8000/tasks")
      .then((res) => res.json())
      .then((data) => {
        if (!cancelled) setTasks(data);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [refreshKey]);

  const markDone = async (taskId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/tasks/${taskId}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "completed" }),
      });
      if (res.ok) {
        setTasks((prev) =>
          prev.map((t) => (t.id === taskId ? { ...t, status: "completed" } : t))
        );
      }
    } catch {
      // Error handled silently
    }
  };

  const pendingTasks = tasks.filter((t) => t.status !== "completed");
  const urgentTasks = pendingTasks.filter(
    (t) => t.priority_indicator || (t.deadline && ["asap", "tonight", "today", "right now"].includes(t.deadline.toLowerCase()))
  );

  return (
    <div className="p-6 space-y-8">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Good morning, Hamza
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            You have{" "}
            <span className="font-medium text-foreground">{pendingTasks.length} task{pendingTasks.length !== 1 ? "s" : ""}</span>{" "}
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
          <p className="mt-3 text-3xl font-bold">{urgentTasks.length}</p>
        </div>
        <div className="rounded-xl border bg-card p-5">
          <div className="flex items-center gap-3">
            <span className="size-2.5 rounded-full bg-yellow-500" />
            <span className="text-sm text-muted-foreground">Pending</span>
          </div>
          <p className="mt-3 text-3xl font-bold">{pendingTasks.length}</p>
        </div>
        <div className="rounded-xl border bg-card p-5">
          <div className="flex items-center gap-3">
            <span className="size-2.5 rounded-full bg-emerald-500" />
            <span className="text-sm text-muted-foreground">Completed</span>
          </div>
          <p className="mt-3 text-3xl font-bold">{tasks.length - pendingTasks.length}</p>
        </div>
      </div>

      {/* Needs attention */}
      <div>
        <h2 className="mb-4 text-lg font-semibold">Needs Your Attention</h2>
        <div className="space-y-3">
          {pendingTasks.length === 0 ? (
            <p className="text-sm text-muted-foreground">No pending tasks.</p>
          ) : (
            pendingTasks.slice(0, 5).map((task) => (
              <div
                key={task.id}
                className="flex items-center justify-between rounded-xl border bg-card p-4"
              >
                <div className="flex items-center gap-4">
                  <span className={`size-2.5 shrink-0 rounded-full ${task.priority_indicator ? "bg-red-500" : "bg-yellow-500"}`} />
                  <div>
                    <p className="text-sm font-medium">{task.description}</p>
                    <p className="text-xs text-muted-foreground">
                      {task.source_message_preview}
                    </p>
                  </div>
                </div>
                {task.deadline && (
                  <span className="text-xs text-muted-foreground hidden sm:inline">
                    Deadline: {task.deadline}
                  </span>
                )}
                <button
                  onClick={() => markDone(task.id)}
                  className="shrink-0 rounded-lg border px-2 py-1 text-[11px] text-muted-foreground hover:bg-emerald-500/10 hover:text-emerald-400 hover:border-emerald-500/20 transition-colors"
                  title="Mark as done"
                >
                  Done
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Flagged messages */}
      <NeedsAttentionSection refreshKey={refreshKey} />

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
