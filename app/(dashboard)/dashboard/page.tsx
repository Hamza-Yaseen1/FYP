"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, CheckSquare, Inbox, Sparkles } from "lucide-react";
import { GlassCard } from "@/components/GlassCard";
import HealthBadge from "@/components/HealthBadge";
import MessageList from "@/components/MessageList";
import NeedsAttentionSection from "@/components/NeedsAttentionSection";
import SimulateMessage from "@/components/SimulateMessage";
import BulkTestButton from "@/components/BulkTestButton"; // TEMPORARY - for load testing
import { Button } from "@/components/ui/button";
import { apiFetch, clearCache } from "@/lib/api";

interface Task {
  id: string;
  description: string;
  deadline: string | null;
  priority_indicator: string | null;
  status: string;
  source_message_preview: string;
  created_at: string;
}

interface User {
  id: string;
  name: string;
  email: string;
}

interface Counts {
  tabs?: {
    all: number;
    urgent: number;
    important: number;
    normal: number;
    unread: number;
  };
}

interface FeedMessage {
  id: string;
  ai_analysis?: {
    recommended_action?: string;
  };
}

// Helper function to get greeting based on time of day
function getGreeting(): string {
  const hour = new Date().getHours();
  return hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
}

export default function DashboardPage() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [userName, setUserName] = useState<string>("User");
  const [counts, setCounts] = useState<Counts | null>(null);
  const [suggestionCount, setSuggestionCount] = useState(0);

  // Fetch current user
  useEffect(() => {
    let cancelled = false;
    apiFetch<User>("/auth/me")
      .then((data) => {
        if (!cancelled) setUserName(data.name);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  // Fetch tasks
  useEffect(() => {
    let cancelled = false;
    apiFetch<Task[]>("/tasks")
      .then((data) => {
        if (!cancelled) setTasks(data);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [refreshKey]);

  // Fetch inbox rollups (counts + AI suggestion count)
  useEffect(() => {
    let cancelled = false;
    apiFetch<Counts>("/messages/counts")
      .then((data) => {
        if (!cancelled) setCounts(data);
      })
      .catch(() => {});
    apiFetch<{ messages: FeedMessage[] }>("/messages")
      .then((data) => {
        if (!cancelled) {
          setSuggestionCount(
            (data.messages || []).filter(
              (m) => m.ai_analysis?.recommended_action
            ).length
          );
        }
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
      clearCache();
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, status: "completed" } : t))
      );
    } catch {
      // Error handled silently
    }
  };

  const pendingTasks = tasks.filter((t) => t.status !== "completed");

  const statCards = [
    {
      label: "Total Messages",
      value: counts?.tabs?.all ?? 0,
      icon: Inbox,
      tint: "bg-signal-dim/70 text-signal",
    },
    {
      label: "High Priority",
      value: counts?.tabs?.urgent ?? 0,
      icon: AlertTriangle,
      tint: "bg-ember-dim/70 text-ember",
    },
    {
      label: "Pending Tasks",
      value: pendingTasks.length,
      icon: CheckSquare,
      tint: "bg-cool-dim/70 text-cool",
    },
    {
      label: "AI Suggestions",
      value: suggestionCount,
      icon: Sparkles,
      tint: "bg-signal-dim/70 text-primary",
    },
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            {getGreeting()}, {userName}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            You have{" "}
            <span className="font-medium text-foreground">{pendingTasks.length} task{pendingTasks.length !== 1 ? "s" : ""}</span>{" "}
            needing attention.
          </p>
        </div>
        <HealthBadge />
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <GlassCard key={stat.label} className="flex items-center gap-4 p-5">
            <span
              className={`flex size-11 shrink-0 items-center justify-center rounded-xl ${stat.tint}`}
            >
              <stat.icon size={20} strokeWidth={1.75} />
            </span>
            <div className="min-w-0">
              <p className="triage-label truncate text-muted-foreground">
                {stat.label}
              </p>
              <p className="mt-1 text-3xl font-semibold tracking-tight">
                {stat.value}
              </p>
            </div>
          </GlassCard>
        ))}
      </div>

      {/* Top 5 pending tasks */}
      <GlassCard className="p-5 sm:p-6">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="triage-label text-muted-foreground">Top tasks</h2>
          <span className="rounded-full border border-border bg-muted/60 px-2 py-0.5 font-mono text-[11px] font-medium text-muted-foreground">
            {pendingTasks.length} pending
          </span>
        </div>
        {pendingTasks.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border py-10 text-center">
            <p className="text-sm text-muted-foreground">No pending tasks. You&apos;re all caught up.</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {pendingTasks.slice(0, 5).map((task) => (
              <div
                key={task.id}
                className="pastel-border glass-card flex items-center justify-between gap-4 rounded-xl p-4"
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
                  className="shrink-0 rounded-full"
                >
                  Done
                </Button>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* NeedAttention feed */}
      <GlassCard className="p-5 sm:p-6">
        <div className="mb-4">
          <h2 className="triage-label text-muted-foreground">Needs your attention</h2>
        </div>
        <NeedsAttentionSection
          refreshKey={refreshKey}
          title=""
          emptyMessage="No items need your attention right now — all quiet."
        />
      </GlassCard>

      {/* Recent messages */}
      <GlassCard className="p-5 sm:p-6">
        <div className="mb-4">
          <h2 className="triage-label text-muted-foreground">Recent messages</h2>
        </div>
        <MessageList refreshKey={refreshKey} />
      </GlassCard>

      {/* Simulate message */}
      <GlassCard className="p-5 sm:p-6">
        <h2 className="triage-label mb-3 text-muted-foreground">Simulate a message</h2>
        <SimulateMessage
          onSent={() => setRefreshKey((k) => k + 1)}
        />
      </GlassCard>

      {/* TEMPORARY - Bulk load testing */}
      <section className="rounded-xl border border-dashed border-yellow-500/50 bg-yellow-50/50 p-5 dark:bg-yellow-950/20">
        <BulkTestButton onComplete={() => setRefreshKey((k) => k + 1)} />
      </section>
    </div>
  );
}