"use client";

import { useEffect, useState } from "react";
import { timeAgo } from "@/lib/time-ago";
import { apiFetch } from "@/lib/api";

interface Task {
  id: string;
  description: string;
  deadline: string | null;
  priority_indicator: string | null;
  requires_action: boolean;
  status: string;
  source_message_id: string;
  source_message_preview: string;
  created_at: string;
}

const statusColors: Record<string, { badge: string; lamp: string }> = {
  pending: {
    badge: "border-primary/25 bg-primary/10 text-primary",
    lamp: "bg-primary",
  },
  in_progress: {
    badge: "border-cool/25 bg-cool/10 text-cool",
    lamp: "bg-cool",
  },
  completed: {
    badge: "border-border bg-muted text-muted-foreground",
    lamp: "bg-dim",
  },
};

export default function TaskList({ refreshKey }: { refreshKey?: number }) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    apiFetch<Task[]>("/tasks")
      .then((data) => {
        if (!cancelled) {
          setTasks(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [refreshKey]);

  const handleStatusChange = async (taskId: string, newStatus: string) => {
    try {
      await apiFetch(`/tasks/${taskId}/status`, {
        method: "PUT",
        body: JSON.stringify({ status: newStatus }),
      });
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t))
      );
    } catch {
      // Error handled silently
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="size-5 animate-spin rounded-full border-2 border-muted border-t-foreground" />
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border py-12 text-center">
        <p className="text-sm text-muted-foreground">No tasks yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {tasks.map((task) => {
        const st = statusColors[task.status] ?? statusColors.pending;
        return (
        <div
          key={task.id}
          className="flex items-start gap-4 rounded-xl border border-border bg-card p-4 transition-colors hover:border-muted-foreground/25"
        >
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium">{task.description}</p>
            <p className="mt-1 line-clamp-1 text-xs text-muted-foreground">
              {task.source_message_preview}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <span
                className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-medium ${st.badge}`}
              >
                <span className={`signal-lamp size-1.5 ${st.lamp}`} aria-hidden />
                {task.status === "in_progress" ? "in progress" : task.status}
              </span>
              {task.deadline && (
                <span className="rounded-full border border-primary/25 bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                  by {task.deadline}
                </span>
              )}
              {task.priority_indicator && (
                <span className="rounded-full border border-ember/25 bg-ember/10 px-2 py-0.5 text-[10px] font-medium text-ember">
                  {task.priority_indicator}
                </span>
              )}
              <span className="font-mono text-[10px] text-muted-foreground">
                {timeAgo(task.created_at)}
              </span>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            {task.status === "pending" && (
              <button
                onClick={() => handleStatusChange(task.id, "in_progress")}
                className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                Start
              </button>
            )}
            {task.status === "in_progress" && (
              <button
                onClick={() => handleStatusChange(task.id, "completed")}
                className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                Done
              </button>
            )}
            {task.status === "completed" && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                <span className="signal-lamp size-1.5 bg-dim" aria-hidden />
                done
              </span>
            )}
          </div>
        </div>
        );
      })}
    </div>
  );
}
