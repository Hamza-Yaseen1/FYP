"use client";

import { useState, useCallback } from "react";
import { Badge } from "@/components/ui/badge";
import { timeAgo } from "@/lib/time-ago";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

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
  updated_at: string | null;
  snoozed_until: string | null;
}

const priorityConfig: Record<string, { emoji: string; color: string; label: string }> = {
  urgent: { emoji: "🔴", color: "text-red-500", label: "Urgent priority" },
  important: { emoji: "🟡", color: "text-yellow-500", label: "Important priority" },
  normal: { emoji: "🟢", color: "text-green-500", label: "Normal priority" },
};

interface TaskCardProps {
  task: Task;
  onComplete: (taskId: string) => Promise<void>;
  onSnooze: (taskId: string, duration: string) => Promise<void>;
  onViewMessage: (taskId: string) => void;
}

export default function TaskCard({
  task,
  onComplete,
  onSnooze,
  onViewMessage,
}: TaskCardProps) {
  const [isCompleting, setIsCompleting] = useState(false);
  const [isSnoozing, setIsSnoozing] = useState(false);

  const priority = task.priority_indicator || "normal";
  const config = priorityConfig[priority] || priorityConfig.normal;

  const handleComplete = async () => {
    setIsCompleting(true);
    try {
      await onComplete(task.id);
    } finally {
      setIsCompleting(false);
    }
  };

  const handleSnooze = async (duration: string) => {
    setIsSnoozing(true);
    try {
      await onSnooze(task.id, duration);
    } finally {
      setIsSnoozing(false);
    }
  };

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleComplete();
      } else if (e.key === "s" || e.key === "S") {
        e.preventDefault();
        handleSnooze("1hour");
      } else if (e.key === "v" || e.key === "V") {
        e.preventDefault();
        onViewMessage(task.id);
      }
    },
    [task.id, handleComplete, handleSnooze, onViewMessage]
  );

  return (
    <div
      className="flex items-start gap-4 rounded-xl border bg-card p-4 transition-colors hover:border-white/10 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      role="article"
      aria-label={`Task: ${task.description}`}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className={config.color} aria-label={config.label}>
            {config.emoji}
          </span>
          <p className="text-sm font-medium">{task.description}</p>
        </div>
        {task.deadline && (
          <p className="mt-1 text-xs text-muted-foreground">
            Due: {task.deadline}
          </p>
        )}
        <div className="mt-2 flex flex-wrap gap-2">
          <span className="text-[10px] text-muted-foreground">
            {timeAgo(task.created_at)}
          </span>
        </div>
      </div>
      <div className="flex shrink-0 gap-1">
        {task.status !== "completed" && (
          <>
            <button
              onClick={handleComplete}
              disabled={isCompleting}
              className="rounded-lg border px-2 py-1 text-[10px] hover:bg-secondary transition-colors disabled:opacity-50"
              aria-label={isCompleting ? "Completing task..." : "Complete task"}
            >
              {isCompleting ? "Completing..." : "Complete"}
            </button>
            <DropdownMenu>
              <DropdownMenuTrigger
                render={
                  <button
                    disabled={isSnoozing}
                    className="rounded-lg border px-2 py-1 text-[10px] hover:bg-secondary transition-colors disabled:opacity-50"
                    aria-label={isSnoozing ? "Snoozing task..." : "Snooze task"}
                  />
                }
              >
                {isSnoozing ? "Snoozing..." : "Snooze"}
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => handleSnooze("1hour")}>
                  1 hour
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleSnooze("tomorrow")}>
                  Tomorrow
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleSnooze("nextweek")}>
                  Next week
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <button
              onClick={() => onViewMessage(task.id)}
              className="rounded-lg border px-2 py-1 text-[10px] hover:bg-secondary transition-colors"
              aria-label="View source message"
            >
              View
            </button>
          </>
        )}
        {task.status === "completed" && (
          <Badge className="text-[10px] bg-emerald-500/15 text-emerald-400 border-emerald-500/20">
            Done
          </Badge>
        )}
      </div>
    </div>
  );
}