"use client";

import { useEffect, useState } from "react";
import { ArrowRight, Mail, MessageCircle, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import PriorityBadge from "@/components/PriorityBadge";
import { useTimeAgo } from "@/lib/use-time-ago";
import { apiFetch } from "@/lib/api";

interface Message {
  id: string;
  sender: string;
  content: string;
  source: string;
  status: string;
  state: string;
  ai_analysis?: {
    priority: string;
    confidence: number;
    explanation?: string;
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

const sourceColors: Record<string, string> = {
  whatsapp: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  gmail: "bg-blue-500/15 text-blue-400 border-blue-500/20",
};

const sourceIcons: Record<string, typeof Mail> = {
  whatsapp: MessageCircle,
  gmail: Mail,
};

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
    apiFetch<{ messages: Message[]; total: number; limit: number; offset: number }>("/messages")
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

  const handleDelete = async () => {
    if (!deleteId) return;
    setDeleting(true);
    try {
      await apiFetch(`/messages/${deleteId}`, { method: "DELETE" });
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
      <div className="rounded-xl border border-dashed py-12 text-center">
        <p className="text-sm text-muted-foreground">
          No messages yet. Simulate one below.
        </p>
      </div>
    );
  }

  const sortedMessages = sortByPriority(messages);

  return (
    <>
      <div className="space-y-3">
        {sortedMessages.map((msg) => (
          <MessageCard key={msg.id} message={msg} onDelete={() => setDeleteId(msg.id)} />
        ))}
      </div>

      {/* Delete Confirmation Dialog */}
      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="rounded-xl bg-card p-6 shadow-lg border max-w-sm w-full mx-4">
            <h3 className="text-lg font-semibold">Delete Message</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Are you sure you want to delete this message? This action cannot be undone.
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setDeleteId(null)}
                disabled={deleting}
                className="px-4 py-2 text-sm rounded-lg border hover:bg-secondary transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-4 py-2 text-sm rounded-lg bg-red-500 text-white hover:bg-red-600 transition-colors disabled:opacity-50"
              >
                {deleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
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
  const SourceIcon = sourceIcons[msg.source.toLowerCase()] ?? Mail;

  return (
    <article className="rounded-xl border bg-card p-4 transition-colors hover:border-white/10">
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-secondary text-sm font-semibold text-secondary-foreground">
          {msg.sender.charAt(0).toUpperCase()}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          {/* Sender + badges */}
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="text-sm font-semibold">{msg.sender}</span>
            <Badge
              variant="outline"
              className={`gap-1 text-[10px] uppercase ${sourceColors[msg.source] ?? ""}`}
            >
              <SourceIcon className="size-3" aria-hidden />
              {msg.source}
            </Badge>
            {msg.status === "unread" && (
              <Badge className="text-[10px] bg-blue-500/15 text-blue-400 border-blue-500/20">
                Unread
              </Badge>
            )}
            {analysis?.tasks_extracted && analysis.tasks_extracted.length > 0 && (
              <Badge className="text-[10px] bg-violet-500/15 text-violet-400 border-violet-500/20">
                {analysis.tasks_extracted.length} task{analysis.tasks_extracted.length !== 1 ? "s" : ""}
              </Badge>
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
              />
            </div>
          )}

          {/* Original message */}
          <p className="mt-2 text-sm leading-relaxed text-foreground/90 line-clamp-2">
            {msg.content}
          </p>

          {/* AI analysis */}
          {(analysis?.summary || analysis?.recommended_action) && (
            <div className="mt-3 space-y-2.5 border-t pt-3">
              {analysis.summary && (
                <div>
                  <p className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
                    <Sparkles className="size-3" aria-hidden />
                    Summary
                  </p>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    {analysis.summary}
                  </p>
                </div>
              )}
              {analysis.recommended_action && (
                <div className="rounded-lg border border-blue-500/20 bg-blue-500/[0.07] p-3">
                  <p className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-blue-400">
                    <ArrowRight className="size-3" aria-hidden />
                    Recommended Action
                  </p>
                  <p className="mt-1 text-xs leading-relaxed text-blue-100/90">
                    {analysis.recommended_action}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Time + Delete */}
        <div className="flex shrink-0 flex-col items-end gap-2">
          <span className="whitespace-nowrap text-xs text-muted-foreground">
            {timeLabel}
          </span>
          <button
            onClick={onDelete}
            className="text-muted-foreground/50 hover:text-red-500 transition-colors"
            title="Delete message"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 6h18" />
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
            </svg>
          </button>
        </div>
      </div>
    </article>
  );
}
