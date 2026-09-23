"use client";

import { useEffect, useState } from "react";
import { Trash2, Loader2 } from "lucide-react";
import PriorityBadge from "@/components/PriorityBadge";
import ConfirmDialog from "@/components/ConfirmDialog";
import { useTimeAgo } from "@/lib/use-time-ago";
import { apiFetch, clearCache } from "@/lib/api";

interface Message {
  id: string;
  sender: string;
  content: string;
  source: string;
  status: string;
  state: string;
  subject?: string;
  ai_analysis?: {
    priority: string;
    confidence: number;
    explanation?: string;
    status?: string;
    summary?: string;
    recommended_action?: string;
    deadlines?: string[];
    needs_attention?: boolean;
    attention_reason?: string;
    tasks_extracted?: Array<{
      description: string;
      deadline: string | null;
      priority_indicator: string | null;
      requires_action: boolean;
    }>;
  };
  created_at: string;
}

type MessagesPayload = {
  messages: Message[];
  total: number;
  limit: number;
  offset: number;
};

const POLL_INTERVAL_MS = 2500;

const priorityOrder: Record<string, number> = {
  urgent: 0,
  important: 1,
  normal: 2,
  low: 3,
  pending: 4,
};

function sortByPriority(messages: Message[]): Message[] {
  return [...messages].sort((a, b) => {
    const aPriority = a.ai_analysis?.priority || "pending";
    const bPriority = b.ai_analysis?.priority || "pending";
    const aOrder = priorityOrder[aPriority] ?? 4;
    const bOrder = priorityOrder[bPriority] ?? 4;
    if (aOrder !== bOrder) return aOrder - bOrder;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
}

export default function MessageList({ refreshKey }: { refreshKey: number }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiFetch<MessagesPayload>("/messages")
      .then((data) => {
        if (!cancelled) {
          setMessages(data.messages || []);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [refreshKey]);

  // Poll quietly while any message is still awaiting analysis. POST /messages
  // analyzes in the background, so un-analysed messages show up right away and
  // resolve async. Each poll bypasses the cache so it sees fresh results.
  useEffect(() => {
    const hasPending = messages.some((m) => !m.ai_analysis);
    if (!hasPending) return;
    const interval = setInterval(async () => {
      try {
        const data = await apiFetch<MessagesPayload>("/messages", {
          cache: "no-store",
        });
        setMessages(data.messages || []);
      } catch {
        // keep the current list; the next tick retries
      }
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [messages]);

  const handleDelete = async () => {
    if (!deleteId) return;
    setDeleting(true);
    try {
      await apiFetch(`/messages/${deleteId}`, { method: "DELETE" });
      clearCache();
      setMessages((prev) => prev.filter((m) => m.id !== deleteId));
    } catch {
      // Error handled silently
    } finally {
      setDeleting(false);
      setDeleteId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="size-5 animate-spin rounded-full border-2 border-muted border-t-foreground" />
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border py-12 text-center">
        <p className="text-sm text-muted-foreground">
          No messages yet. Simulate one below.
        </p>
      </div>
    );
  }

  const sortedMessages = sortByPriority(messages);

  return (
    <>
      <div className="space-y-2.5">
        {sortedMessages.map((msg) => (
          <MessageCard key={msg.id} message={msg} onDelete={() => setDeleteId(msg.id)} />
        ))}
      </div>

      {deleteId && (
        <ConfirmDialog
          open
          title="Delete message"
          description="Are you sure you want to delete this message? This action cannot be undone."
          confirmLabel={deleting ? "Deleting…" : "Delete"}
          confirmVariant="destructive"
          loading={deleting}
          onConfirm={handleDelete}
          onCancel={() => setDeleteId(null)}
        />
      )}
    </>
  );
}

function MessageCard({
  message: msg,
  onDelete,
}: {
  message: Message;
  onDelete: () => void;
}) {
  const timeLabel = useTimeAgo(msg.created_at);
  const analysis = msg.ai_analysis;

  return (
    <article className="pastel-border glass-card rounded-2xl p-4 shadow-sm transition-all duration-300 hover:shadow-md">
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold text-muted-foreground">
          {msg.sender.charAt(0).toUpperCase()}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          {/* Sender + badges */}
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="text-sm font-medium text-foreground">{msg.sender}</span>
            <span className="rounded-full border border-border bg-muted px-2 py-0.5 text-[10px] font-medium tracking-wide text-muted-foreground uppercase">
              {msg.source}
            </span>
            {msg.status === "unread" && (
              <span className="rounded-full border border-primary/25 bg-primary/10 px-2 py-0.5 text-[10px] font-medium tracking-wide text-primary uppercase">
                unread
              </span>
            )}
            {!analysis && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium tracking-wide text-amber-600 uppercase">
                <Loader2 className="size-3 animate-spin" aria-hidden />
                Analyzing…
              </span>
            )}
            {analysis?.tasks_extracted && analysis.tasks_extracted.length > 0 && (
              <span className="rounded-full border border-border bg-muted px-2 py-0.5 text-[10px] font-medium tracking-wide text-muted-foreground uppercase">
                {analysis.tasks_extracted.length} task{analysis.tasks_extracted.length !== 1 ? "s" : ""}
              </span>
            )}
          </div>

          {/* Priority + confidence */}
          {analysis && (
            <div className="mt-1.5">
              <PriorityBadge
                messageId={msg.id}
                priority={analysis.priority}
                confidence={analysis.confidence}
                explanation={analysis.explanation}
                status={analysis.status}
              />
            </div>
          )}

          {/* Subject line (Gmail messages) */}
          {msg.subject && (
            <p className="mt-1.5 text-sm font-medium text-foreground">
              Re: {msg.subject}
            </p>
          )}

          {/* Original message */}
          <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-foreground/90">
            {msg.content}
          </p>

          {/* AI analysis */}
          {(analysis?.summary || analysis?.recommended_action) && (
            <div className="mt-3 space-y-2.5 border-t border-border pt-3">
              {analysis.summary && (
                <div>
                  <p className="triage-label text-muted-foreground/70">Summary</p>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    {analysis.summary}
                  </p>
                </div>
              )}
              {analysis.recommended_action && (
                <div className="rounded-lg bg-muted/60 p-3">
                  <p className="triage-label text-primary">Recommended action</p>
                  <p className="mt-1 text-xs leading-relaxed text-foreground/90">
                    {analysis.recommended_action}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Time + Delete */}
        <div className="flex shrink-0 flex-col items-end gap-2">
          <span className="whitespace-nowrap font-mono text-[11px] text-muted-foreground">
            {timeLabel}
          </span>
          <button
            onClick={onDelete}
            className="rounded-md p-1 text-muted-foreground/50 transition-colors hover:bg-destructive/10 hover:text-destructive"
            title="Delete message"
            aria-label="Delete message"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
    </article>
  );
}