"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { timeAgo } from "@/lib/time-ago";

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

const statusColors: Record<string, string> = {
  pending: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
  in_progress: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  completed: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
};

export default function TaskList({ refreshKey }: { refreshKey?: number }) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetch("http://localhost:8000/tasks")
      .then((res) => res.json())
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
      const res = await fetch(`http://localhost:8000/tasks/${taskId}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        setTasks((prev) =>
          prev.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t))
        );
      }
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
      <div className="rounded-xl border border-dashed py-12 text-center">
        <p className="text-sm text-muted-foreground">No tasks yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <div
          key={task.id}
          className="flex items-start gap-4 rounded-xl border bg-card p-4 transition-colors hover:border-white/10"
        >
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium">{task.description}</p>
            <p className="mt-1 text-xs text-muted-foreground line-clamp-1">
              {task.source_message_preview}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <Badge
                variant="outline"
                className={`text-[10px] uppercase ${statusColors[task.status] ?? ""}`}
              >
                {task.status}
              </Badge>
              {task.deadline && (
                <Badge className="text-[10px] bg-orange-500/15 text-orange-400 border-orange-500/20">
                  {task.deadline}
                </Badge>
              )}
              {task.priority_indicator && (
                <Badge className="text-[10px] bg-red-500/15 text-red-400 border-red-500/20">
                  {task.priority_indicator}
                </Badge>
              )}
              <span className="text-[10px] text-muted-foreground">
                {timeAgo(task.created_at)}
              </span>
            </div>
          </div>
          <div className="flex shrink-0 gap-1">
            {task.status === "pending" && (
              <button
                onClick={() => handleStatusChange(task.id, "in_progress")}
                className="rounded-lg border px-2 py-1 text-[10px] hover:bg-secondary transition-colors"
              >
                Start
              </button>
            )}
            {task.status === "in_progress" && (
              <button
                onClick={() => handleStatusChange(task.id, "completed")}
                className="rounded-lg border px-2 py-1 text-[10px] hover:bg-secondary transition-colors"
              >
                Done
              </button>
            )}
            {task.status === "completed" && (
              <Badge className="text-[10px] bg-emerald-500/15 text-emerald-400 border-emerald-500/20">
                Done
              </Badge>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
