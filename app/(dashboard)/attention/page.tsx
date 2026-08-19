import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Attention — Communication AI",
};

export default function AttentionPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold tracking-tight">Attention</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Items that need your immediate attention.
      </p>
      <div className="mt-8 flex flex-col items-center justify-center rounded-xl border border-dashed py-20">
        <p className="text-sm text-muted-foreground">No items requiring attention.</p>
      </div>
    </div>
  );
}
