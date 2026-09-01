import type { Metadata } from "next";
import TaskList from "@/components/tasks/TaskList";

export const metadata: Metadata = {
  title: "Tasks — Communication AI",
};

export default function TasksPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">My Tasks</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Pulled from your messages, sorted by priority
      </p>
      <div className="mt-6">
        <TaskList />
      </div>
    </div>
  );
}