import type { Metadata } from "next";
import NeedsAttentionSection from "@/components/NeedsAttentionSection";

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
      <div className="mt-8">
        <NeedsAttentionSection
          refreshKey={0}
          title=""
          emptyMessage="No items requiring attention."
        />
      </div>
    </div>
  );
}
