"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getTasks, completeTask, snoozeTask } from "@/lib/api/tasks";
import TaskCard from "./TaskCard";
import LoadingSkeleton from "@/components/LoadingSkeleton";

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

export default function TaskList({ refreshKey }: { refreshKey?: number }) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;
    getTasks()
      .then((data) => {
        if (!cancelled) {
          setTasks(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  const handleComplete = async (taskId: string) => {
    await completeTask(taskId);
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
  };

  const handleSnooze = async (taskId: string, duration: string) => {
    await snoozeTask(taskId, duration);
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
  };

  const handleViewMessage = (taskId: string) => {
    // Navigate to inbox with message ID
    router.push(`/inbox?messageId=${taskId}`);
  };

  if (loading) {
    return <LoadingSkeleton count={3} />;
  }

  if (tasks.length === 0) {
    return (
      <div className="rounded-xl border border-dashed py-12 text-center">
        <p className="text-sm text-muted-foreground">No tasks found</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <TaskCard
          key={task.id}
          task={task}
          onComplete={handleComplete}
          onSnooze={handleSnooze}
          onViewMessage={handleViewMessage}
        />
      ))}
    </div>
  );
}