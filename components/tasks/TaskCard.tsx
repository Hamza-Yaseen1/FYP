"use client";

import { useState, useCallback } from "react";
import { timeAgo } from "@/lib/time-ago";
import { Button } from "@/components/ui/button";
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

const priorityConfig: Record<
  string,
  { badge: string; dot: string; label: string }
> = {
  urgent: {
    badge: "border-ember/25 bg-ember/10 text-ember",
    dot: "bg-ember",
    label: "Urgent priority",
  },
  important: {
    badge: "border-primary/25 bg-primary/10 text-primary",
    dot: "bg-primary",
    label: "Important priority",
  },
  normal: {
    badge: "border-cool/25 bg-cool/10 text-cool",
    dot: "bg-cool",
    label: "Normal priority",
  },
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

  const handleComplete = useCallback(async () => {
    setIsCompleting(true);
    try {
      await onComplete(task.id);
    } finally {
      setIsCompleting(false);
    }
  }, [onComplete, task.id]);

  const handleSnooze = useCallback(async (duration: string) => {
    setIsSnoozing(true);
    try {
      await onSnooze(task.id, duration);
    } finally {
      setIsSnoozing(false);
    }
  }, [onSnooze, task.id]);

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
      className="pastel-border glass-card flex items-start gap-4 rounded-2xl p-4 shadow-sm transition-all duration-300 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1 focus:ring-offset-background"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      role="article"
      aria-label={`Task: ${task.description}`}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2.5">
          <span className={`signal-lamp size-2 shrink-0 ${config.dot}`} aria-hidden />
          <p className="text-sm font-medium">{task.description}</p>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <span
            className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium ${config.badge}`}
          >
            {config.label}
          </span>
          {task.deadline && (
            <span className="font-mono text-[11px] text-muted-foreground">
              by {task.deadline}
            </span>
          )}
          <span className="font-mono text-[11px] text-muted-foreground">
            {timeAgo(task.created_at)}
          </span>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-1.5">
        {task.status !== "completed" && (
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={handleComplete}
              disabled={isCompleting}
              aria-label={isCompleting ? "Completing task..." : "Complete task"}
            >
              {isCompleting ? "Completing…" : "Complete"}
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger
                render={
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={isSnoozing}
                    aria-label={isSnoozing ? "Snoozing task..." : "Snooze task"}
                  />
                }
              >
                {isSnoozing ? "Snoozing…" : "Snooze"}
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
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onViewMessage(task.id)}
              aria-label="View source message"
            >
              View
            </Button>
          </>
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
}