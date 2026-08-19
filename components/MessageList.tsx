"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { timeAgo } from "@/lib/time-ago";

interface Message {
  id: string;
  sender: string;
  content: string;
  source: string;
  status: string;
  created_at: string;
}

const sourceColors: Record<string, string> = {
  whatsapp: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  gmail: "bg-blue-500/15 text-blue-400 border-blue-500/20",
};

export default function MessageList({ refreshKey }: { refreshKey: number }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);

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

  return (
    <div className="space-y-3">
      {messages.map((msg) => (
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
            </div>
            <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
              {msg.content}
            </p>
          </div>

          {/* Time */}
          <span className="shrink-0 text-xs text-muted-foreground">
            {timeAgo(msg.created_at)}
          </span>
        </div>
      ))}
    </div>
  );
}
