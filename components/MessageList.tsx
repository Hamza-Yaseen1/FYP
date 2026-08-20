"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import PriorityBadge from "@/components/PriorityBadge";
import { timeAgo } from "@/lib/time-ago";

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
    fetch("http://localhost:8000/messages")
      .then((res) => res.json())
      .then((data) => {
        if (!cancelled) {
          setMessages(data);
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
      const res = await fetch(`http://localhost:8000/messages/${deleteId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setMessages((prev) => prev.filter((m) => m.id !== deleteId));
      }
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
          <div
            key={msg.id}
            className="flex items-start gap-4 rounded-xl border bg-card p-4 transition-colors hover:border-white/10"
          >
            {/* Avatar */}
            <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-secondary text-sm font-semibold text-secondary-foreground">
              {msg.sender.charAt(0).toUpperCase()}
            </div>

            {/* Content */}
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-semibold">{msg.sender}</span>
                <Badge
                  variant="outline"
                  className={`text-[10px] uppercase ${sourceColors[msg.source] ?? ""}`}
                >
                  {msg.source}
                </Badge>
                {msg.status === "unread" && (
                  <Badge className="text-[10px] bg-blue-500/15 text-blue-400 border-blue-500/20">
                    Unread
                  </Badge>
                )}
                {msg.ai_analysis?.tasks_extracted && msg.ai_analysis.tasks_extracted.length > 0 && (
                  <Badge className="text-[10px] bg-violet-500/15 text-violet-400 border-violet-500/20">
                    {msg.ai_analysis.tasks_extracted.length} task{msg.ai_analysis.tasks_extracted.length !== 1 ? "s" : ""}
                  </Badge>
                )}
                {msg.ai_analysis && (
                  <PriorityBadge
                    messageId={msg.id}
                    priority={msg.ai_analysis.priority}
                    confidence={msg.ai_analysis.confidence}
                    explanation={msg.ai_analysis.explanation}
                  />
                )}
              </div>
              <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                {msg.content}
              </p>
              {msg.ai_analysis?.summary && (
                <p className="mt-2 text-xs text-muted-foreground/70 italic">
                  {msg.ai_analysis.summary}
                </p>
              )}
            </div>

            {/* Time + Delete */}
            <div className="flex flex-col items-end gap-2">
              <span className="shrink-0 text-xs text-muted-foreground">
                {timeAgo(msg.created_at)}
              </span>
              <button
                onClick={() => setDeleteId(msg.id)}
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
