import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Inbox — Communication AI",
};

export default function InboxPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold tracking-tight">Inbox</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Your messages and conversations.
      </p>
      <div className="mt-8 flex flex-col items-center justify-center rounded-xl border border-dashed py-20">
        <p className="text-sm text-muted-foreground">No messages yet.</p>
      </div>
    </div>
  );
}
