"use client";

import { useEffect, useState } from "react";
import NeedsAttentionCard from "@/components/NeedsAttentionCard";
import { apiFetch } from "@/lib/api";

interface AttentionMessage {
  id: string;
  sender: string;
  source: string;
  created_at: string;
  ai_analysis?: {
    needs_attention?: boolean;
    recommended_action?: string;
    tasks_extracted?: Array<{
      description: string;
      deadline: string | null;
      priority_indicator: string | null;
      requires_action: boolean;
    }>;
    deadlines?: string[];
    attention_reason?: string;
  };
}

export default function NeedsAttentionSection({
  refreshKey,
  title = "Needs Attention",
  emptyMessage,
}: {
  refreshKey: number;
  title?: string;
  emptyMessage?: string;
}) {
  const [messages, setMessages] = useState<AttentionMessage[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiFetch<{ messages: AttentionMessage[]; total: number; limit: number; offset: number }>("/messages")
      .then((data) => {
        if (!cancelled) {
          setMessages(data.messages || []);
          setLoaded(true);
        }
      })
      .catch(() => {
        if (!cancelled) setLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  const flagged = messages.filter((m) => m.ai_analysis?.needs_attention);

  if (loaded && flagged.length === 0) {
    if (!emptyMessage) return null;
    return (
      <div>
        {title && <h2 className="triage-label mb-3 text-muted-foreground">{title}</h2>}
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <p className="text-sm text-muted-foreground">{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {title && (
        <div className="mb-3 flex items-center gap-2">
          <h2 className="triage-label text-muted-foreground">{title}</h2>
          <span className="rounded-full border border-ember/25 bg-ember/10 px-2 py-0.5 font-mono text-[11px] font-medium text-ember">
            {flagged.length}
          </span>
        </div>
      )}
      <div className="space-y-2.5">
        {flagged.map((message) => (
          <NeedsAttentionCard key={message.id} message={message} />
        ))}
      </div>
    </div>
  );
}