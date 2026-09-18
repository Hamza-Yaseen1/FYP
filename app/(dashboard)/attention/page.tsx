import type { Metadata } from "next";
import { GlassCard } from "@/components/GlassCard";
import NeedsAttentionSection from "@/components/NeedsAttentionSection";

export const metadata: Metadata = {
  title: "Attention — Communication Overload Management",
};

export default function AttentionPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Attention</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Items that need you right now
      </p>
      <GlassCard className="mt-6 p-5 sm:p-6">
        <NeedsAttentionSection
          refreshKey={0}
          title=""
          emptyMessage="No items requiring attention."
        />
      </GlassCard>
    </div>
  );
}