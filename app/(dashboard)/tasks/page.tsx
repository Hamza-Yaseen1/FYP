import type { Metadata } from "next";
import TaskList from "@/components/tasks/TaskList";

export const metadata: Metadata = {
  title: "Tasks — Communication AI",
};

export default function TasksPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold tracking-tight">My Tasks</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Tasks extracted from your messages, sorted by priority.
      </p>
      <div className="mt-6">
        <TaskList />
      </div>
    </div>
  );
}
