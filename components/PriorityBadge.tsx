"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
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
  onPriorityChange?: (newPriority: string) => void;
}

const priorityConfig: Record<string, { color: string; label: string }> = {
  urgent: {
    color: "bg-red-500/15 text-red-400 border-red-500/20",
    label: "Urgent",
  },
  important: {
    color: "bg-orange-500/15 text-orange-400 border-orange-500/20",
    label: "Important",
  },
  normal: {
    color: "bg-blue-500/15 text-blue-400 border-blue-500/20",
    label: "Normal",
  },
  low: {
    color: "bg-gray-500/15 text-gray-400 border-gray-500/20",
    label: "Low",
  },
  pending: {
    color: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
    label: "Pending",
  },
};

const priorities = ["urgent", "important", "normal", "low"];

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return "text-green-400";
  if (confidence >= 0.5) return "text-yellow-400";
  return "text-red-400";
}

export default function PriorityBadge({
  messageId,
  priority,
  confidence,
  explanation,
  onPriorityChange,
}: PriorityBadgeProps) {
  const [currentPriority, setCurrentPriority] = useState(priority);
  const [isUpdating, setIsUpdating] = useState(false);

  const config = priorityConfig[currentPriority] || priorityConfig.pending;
  const showReviewFlag = confidence !== undefined && confidence < 0.5;
  const showReviewRecommended =
    confidence !== undefined && confidence >= 0.5 && confidence < 0.8;

  const handlePriorityChange = async (newPriority: string) => {
    if (newPriority === currentPriority) return;

    setIsUpdating(true);
    try {
      const response = await fetch(
        `http://localhost:8000/messages/${messageId}/priority?priority=${newPriority}`,
        { method: "PUT" }
      );

      if (response.ok) {
        setCurrentPriority(newPriority);
        onPriorityChange?.(newPriority);
      }
    } catch (error) {
      console.error("Failed to update priority:", error);
    } finally {
      setIsUpdating(false);
    }
  };

  const tooltipContent = [
    explanation && `Reason: ${explanation}`,
    confidence !== undefined && `Confidence: ${Math.round(confidence * 100)}%`,
  ]
    .filter(Boolean)
    .join("\n");

  return (
    <div className="flex items-center gap-1">
      <DropdownMenu>
        <DropdownMenuTrigger>
          <Badge
            variant="outline"
            className={`text-[10px] uppercase cursor-pointer hover:opacity-80 ${config.color}`}
            title={tooltipContent || undefined}
          >
            {isUpdating ? "Updating..." : config.label}
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
      {confidence !== undefined && (
        <span
          className={`text-[10px] ${getConfidenceColor(confidence)}`}
          title={tooltipContent || undefined}
        >
          {Math.round(confidence * 100)}%
        </span>
      )}
      {showReviewFlag && (
        <Badge className="text-[10px] bg-yellow-500/15 text-yellow-400 border-yellow-500/20">
          Needs review
        </Badge>
      )}
      {showReviewRecommended && (
        <Badge className="text-[10px] bg-yellow-500/15 text-yellow-400 border-yellow-500/20">
          Review
        </Badge>
      )}
    </div>
  );
}
