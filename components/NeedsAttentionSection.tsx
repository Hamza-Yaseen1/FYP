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
        {title && <h2 className="mb-4 text-lg font-semibold">{title}</h2>}
        <div className="rounded-xl border border-dashed py-12 text-center">
          <p className="text-sm text-muted-foreground">{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {title && (
        <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
          {title}
          <span className="rounded-full bg-red-500/15 px-2 py-0.5 text-xs font-medium text-red-400">
            {flagged.length}
          </span>
        </h2>
      )}
      <div className="space-y-3">
        {flagged.map((message) => (
          <NeedsAttentionCard key={message.id} message={message} />
        ))}
      </div>
    </div>
  );
}
