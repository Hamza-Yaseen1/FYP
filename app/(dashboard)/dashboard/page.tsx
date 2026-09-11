"use client";

import { useEffect, useState } from "react";
import HealthBadge from "@/components/HealthBadge";
import MessageList from "@/components/MessageList";
import NeedsAttentionSection from "@/components/NeedsAttentionSection";
import SimulateMessage from "@/components/SimulateMessage";
import BulkTestButton from "@/components/BulkTestButton"; // TEMPORARY - for load testing
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

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
    apiFetch<Task[]>("/tasks")
      .then((data) => {
        if (!cancelled) setTasks(data);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [refreshKey]);

  const markDone = async (taskId: string) => {
    try {
      await apiFetch(`/tasks/${taskId}/status`, {
        method: "PUT",
        body: JSON.stringify({ status: "completed" }),
      });
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, status: "completed" } : t))
      );
    } catch {
      // Error handled silently
    }
  };

  const pendingTasks = tasks.filter((t) => t.status !== "completed");
  const urgentTasks = pendingTasks.filter(
    (t) => t.priority_indicator || (t.deadline && ["asap", "tonight", "today", "right now"].includes(t.deadline.toLowerCase()))
  );
  const completedTasks = tasks.length - pendingTasks.length;

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
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
        <div className="rounded-xl border border-border bg-card p-5">
          <p className="triage-label text-muted-foreground">Urgent</p>
          <p className="mt-2 text-3xl font-semibold tracking-tight">{urgentTasks.length}</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <p className="triage-label text-muted-foreground">Pending</p>
          <p className="mt-2 text-3xl font-semibold tracking-tight text-primary">{pendingTasks.length}</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <p className="triage-label text-muted-foreground">Completed</p>
          <p className="mt-2 text-3xl font-semibold tracking-tight">{completedTasks}</p>
        </div>
      </div>

      {/* Needs attention */}
      <section>
        <h2 className="triage-label mb-3 text-muted-foreground">Needs your attention</h2>
        <div className="space-y-2.5">
          {pendingTasks.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border py-12 text-center">
              <p className="text-sm text-muted-foreground">No pending tasks. You&apos;re all caught up.</p>
            </div>
          ) : (
            pendingTasks.slice(0, 5).map((task) => (
              <div
                key={task.id}
                className="flex items-center justify-between gap-4 rounded-xl border border-border bg-card p-4"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`signal-lamp shrink-0 ${
                      task.priority_indicator ? "bg-ember" : "bg-primary"
                    }`}
                    aria-hidden
                  />
                  <div>
                    <p className="text-sm font-medium">{task.description}</p>
                    <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">
                      {task.source_message_preview}
                    </p>
                  </div>
                </div>
                {task.deadline && (
                  <span className="hidden shrink-0 font-mono text-[11px] text-muted-foreground sm:inline">
                    by {task.deadline}
                  </span>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => markDone(task.id)}
                  className="shrink-0"
                >
                  Done
                </Button>
              </div>
            ))
          )}
        </div>
      </section>

      {/* Flagged messages */}
      <NeedsAttentionSection refreshKey={refreshKey} />

      {/* Recent messages */}
      <section>
        <h2 className="triage-label mb-3 text-muted-foreground">Recent messages</h2>
        <MessageList refreshKey={refreshKey} />
      </section>

      {/* Simulate message */}
      <section className="rounded-xl border border-border bg-card p-5">
        <h2 className="triage-label mb-3 text-muted-foreground">Simulate a message</h2>
        <SimulateMessage
          onSent={() => setRefreshKey((k) => k + 1)}
        />
      </section>

      {/* TEMPORARY - Bulk load testing */}
      <section className="rounded-xl border border-dashed border-yellow-500/50 bg-yellow-50/50 p-5 dark:bg-yellow-950/20">
        <BulkTestButton onComplete={() => setRefreshKey((k) => k + 1)} />
      </section>
    </div>
  );
}