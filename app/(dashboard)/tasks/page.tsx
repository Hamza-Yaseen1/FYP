import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Tasks — Communication AI",
};

export default function TasksPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold tracking-tight">Tasks</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Manage and track your tasks.
      </p>
      <div className="mt-8 flex flex-col items-center justify-center rounded-xl border border-dashed py-20">
        <p className="text-sm text-muted-foreground">No tasks yet.</p>
      </div>
    </div>
  );
}
