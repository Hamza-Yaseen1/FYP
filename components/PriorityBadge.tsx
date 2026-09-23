"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { apiFetch, clearCache } from "@/lib/api";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface PriorityBadgeProps {
  messageId: string;
  priority: string;
  confidence?: number;
  explanation?: string;
  status?: string;
  onPriorityChange?: (newPriority: string) => void;
}

const priorityConfig: Record<string, { color: string; lamp: string; label: string }> = {
  urgent: {
    color: "border-ember/25 bg-ember/10 text-ember",
    lamp: "bg-ember",
    label: "Urgent",
  },
  important: {
    color: "border-primary/25 bg-primary/10 text-primary",
    lamp: "bg-primary",
    label: "Important",
  },
  normal: {
    color: "border-cool/25 bg-cool/10 text-cool",
    lamp: "bg-cool",
    label: "Normal",
  },
  low: {
    color: "border-border bg-muted text-muted-foreground",
    lamp: "bg-dim",
    label: "Low",
  },
  pending: {
    color: "border-amber-500/30 bg-amber-500/10 text-amber-600",
    lamp: "bg-amber-500",
    label: "Pending",
  },
};

const priorities = ["urgent", "important", "normal", "low"];

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return "text-cool";
  if (confidence >= 0.5) return "text-primary";
  return "text-ember";
}

const badgeBase =
  "inline-flex cursor-pointer items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium leading-4 transition-colors hover:opacity-80";

export default function PriorityBadge({
  messageId,
  priority,
  confidence,
  explanation,
  status,
  onPriorityChange,
}: PriorityBadgeProps) {
  const [currentPriority, setCurrentPriority] = useState(priority);

  // Sync local state with the server's classification. Without this, a
  // message whose analysis went pending -> completed (re-analysis, retry
  // sweep, override) would keep showing the STALE badge because useState
  // only reads the prop on first render. This is the render-time adjustment
  // pattern (React docs) — deliberately NOT an effect, so it never fights
  // the optimistic-update state set by handlePriorityChange.
  const [prevPriorityProp, setPrevPriorityProp] = useState(priority);
  if (prevPriorityProp !== priority) {
    setPrevPriorityProp(priority);
    setCurrentPriority(priority);
  }
  const [isUpdating, setIsUpdating] = useState(false);

  // A failed/degraded analysis stores status="pending" with confidence 0.0.
  // Don't present that stub as a real "Normal 0%" classification — show it
  // as Pending instead (it is retried automatically by the backend sweep).
  const isPending = status === "pending";
  const config = priorityConfig[isPending ? "pending" : currentPriority] || priorityConfig.pending;
  const showReviewFlag =
    !isPending && confidence !== undefined && confidence < 0.5;
  const showReviewRecommended =
    !isPending && confidence !== undefined && confidence >= 0.5 && confidence < 0.8;

  const handlePriorityChange = async (newPriority: string) => {
    if (newPriority === currentPriority) return;

    setIsUpdating(true);
    try {
      await apiFetch(
        `/messages/${messageId}/priority?priority=${newPriority}`,
        { method: "PUT" }
      );
      clearCache();

      setCurrentPriority(newPriority);
      onPriorityChange?.(newPriority);
    } catch (error) {
      console.error("Failed to update priority:", error);
    } finally {
      setIsUpdating(false);
    }
  };

  const tooltipContent = [
    isPending
      ? "AI analysis failed or is pending — it will be retried automatically"
      : explanation && `Reason: ${explanation}`,
    !isPending && confidence !== undefined && `Confidence: ${Math.round(confidence * 100)}%`,
  ]
    .filter(Boolean)
    .join("\n");

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <DropdownMenu>
        <DropdownMenuTrigger>
          <Badge
            variant="outline"
            className={`${badgeBase} ${config.color}`}
            title={tooltipContent || undefined}
          >
            <span className={`signal-lamp size-1.5 ${config.lamp}`} aria-hidden />
            {isUpdating ? "Updating…" : config.label}
          </Badge>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          {priorities.map((p) => (
            <DropdownMenuItem
              key={p}
              onClick={() => handlePriorityChange(p)}
              className={p === currentPriority ? "bg-accent" : ""}
            >
              {priorityConfig[p].label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      {!isPending && confidence !== undefined && (
        <span
          className={`font-mono text-[10px] ${getConfidenceColor(confidence)}`}
          title={tooltipContent || undefined}
        >
          {Math.round(confidence * 100)}%
        </span>
      )}
      {showReviewFlag && (
        <Badge
          variant="outline"
          className={`${badgeBase} pointer-events-none border-ember/25 bg-ember/10 text-ember`}
        >
          Review
        </Badge>
      )}
      {showReviewRecommended && (
        <Badge
          variant="outline"
          className={`${badgeBase} pointer-events-none border-primary/25 bg-primary/10 text-primary`}
        >
          Verify
        </Badge>
      )}
    </div>
  );
}