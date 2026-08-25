"use client";

import { useState } from "react";
import { ChevronDown, X, Calendar } from "lucide-react";
import { cn } from "@/lib/utils";

interface FilterOption {
  value: string;
  label: string;
}

interface FilterBarProps {
  sources: FilterOption[];
  priorities: FilterOption[];
  senders: FilterOption[];
  selectedSource: string | null;
  selectedPriority: string | null;
  selectedSender: string | null;
  startDate: string | null;
  endDate: string | null;
  onSourceChange: (source: string | null) => void;
  onPriorityChange: (priority: string | null) => void;
  onSenderChange: (sender: string | null) => void;
  onStartDateChange: (date: string | null) => void;
  onEndDateChange: (date: string | null) => void;
  className?: string;
}

export default function FilterBar({
  sources,
  priorities,
  senders,
  selectedSource,
  selectedPriority,
  selectedSender,
  startDate,
  endDate,
  onSourceChange,
  onPriorityChange,
  onSenderChange,
  onStartDateChange,
  onEndDateChange,
  className,
}: FilterBarProps) {
  const [openDropdown, setOpenDropdown] = useState<"source" | "priority" | "sender" | null>(null);
  const [showDateRange, setShowDateRange] = useState(false);

  const hasActiveFilters = selectedSource || selectedPriority || selectedSender || startDate || endDate;

  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      {/* Source Filter */}
      <div className="relative">
        <button
          onClick={() => setOpenDropdown(openDropdown === "source" ? null : "source")}
          className={cn(
            "flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors",
            selectedSource
              ? "border-primary/50 bg-primary/10 text-primary"
              : "border-border bg-background text-muted-foreground hover:text-foreground"
          )}
        >
          Source
          <ChevronDown className="size-3" />
        </button>
        {openDropdown === "source" && (
          <div className="absolute left-0 top-full z-10 mt-1 w-40 rounded-lg border bg-card shadow-lg">
            <button
              onClick={() => {
                onSourceChange(null);
                setOpenDropdown(null);
              }}
              className={cn(
                "w-full px-3 py-2 text-left text-sm hover:bg-muted",
                !selectedSource && "font-medium text-primary"
              )}
            >
              All Sources
            </button>
            {sources.map((source) => (
              <button
                key={source.value}
                onClick={() => {
                  onSourceChange(source.value);
                  setOpenDropdown(null);
                }}
                className={cn(
                  "w-full px-3 py-2 text-left text-sm hover:bg-muted",
                  selectedSource === source.value && "font-medium text-primary"
                )}
              >
                {source.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Priority Filter */}
      <div className="relative">
        <button
          onClick={() => setOpenDropdown(openDropdown === "priority" ? null : "priority")}
          className={cn(
            "flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors",
            selectedPriority
              ? "border-primary/50 bg-primary/10 text-primary"
              : "border-border bg-background text-muted-foreground hover:text-foreground"
          )}
        >
          Priority
          <ChevronDown className="size-3" />
        </button>
        {openDropdown === "priority" && (
          <div className="absolute left-0 top-full z-10 mt-1 w-40 rounded-lg border bg-card shadow-lg">
            <button
              onClick={() => {
                onPriorityChange(null);
                setOpenDropdown(null);
              }}
              className={cn(
                "w-full px-3 py-2 text-left text-sm hover:bg-muted",
                !selectedPriority && "font-medium text-primary"
              )}
            >
              All Priorities
            </button>
            {priorities.map((priority) => (
              <button
                key={priority.value}
                onClick={() => {
                  onPriorityChange(priority.value);
                  setOpenDropdown(null);
                }}
                className={cn(
                  "w-full px-3 py-2 text-left text-sm hover:bg-muted",
                  selectedPriority === priority.value && "font-medium text-primary"
                )}
              >
                {priority.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Sender Filter */}
      <div className="relative">
        <button
          onClick={() => setOpenDropdown(openDropdown === "sender" ? null : "sender")}
          className={cn(
            "flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors",
            selectedSender
              ? "border-primary/50 bg-primary/10 text-primary"
              : "border-border bg-background text-muted-foreground hover:text-foreground"
          )}
        >
          Sender
          <ChevronDown className="size-3" />
        </button>
        {openDropdown === "sender" && (
          <div className="absolute left-0 top-full z-10 mt-1 w-40 rounded-lg border bg-card shadow-lg">
            <button
              onClick={() => {
                onSenderChange(null);
                setOpenDropdown(null);
              }}
              className={cn(
                "w-full px-3 py-2 text-left text-sm hover:bg-muted",
                !selectedSender && "font-medium text-primary"
              )}
            >
              All Senders
            </button>
            {senders.map((sender) => (
              <button
                key={sender.value}
                onClick={() => {
                  onSenderChange(sender.value);
                  setOpenDropdown(null);
                }}
                className={cn(
                  "w-full px-3 py-2 text-left text-sm hover:bg-muted",
                  selectedSender === sender.value && "font-medium text-primary"
                )}
              >
                {sender.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Date Range Filter */}
      <div className="relative">
        <button
          onClick={() => setShowDateRange(!showDateRange)}
          className={cn(
            "flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors",
            startDate || endDate
              ? "border-primary/50 bg-primary/10 text-primary"
              : "border-border bg-background text-muted-foreground hover:text-foreground"
          )}
        >
          <Calendar className="size-3" />
          Date Range
        </button>
        {showDateRange && (
          <div className="absolute left-0 top-full z-10 mt-1 w-64 rounded-lg border bg-card p-3 shadow-lg">
            <div className="space-y-2">
              <div>
                <label className="text-xs font-medium text-muted-foreground">From</label>
                <input
                  type="date"
                  value={startDate || ""}
                  onChange={(e) => onStartDateChange(e.target.value || null)}
                  className="mt-1 w-full rounded-md border bg-background px-2 py-1 text-sm"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">To</label>
                <input
                  type="date"
                  value={endDate || ""}
                  onChange={(e) => onEndDateChange(e.target.value || null)}
                  className="mt-1 w-full rounded-md border bg-background px-2 py-1 text-sm"
                />
              </div>
              <button
                onClick={() => setShowDateRange(false)}
                className="w-full rounded-md bg-primary px-2 py-1 text-sm text-primary-foreground hover:bg-primary/80"
              >
                Apply
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Clear Filters */}
      {hasActiveFilters && (
        <button
          onClick={() => {
            onSourceChange(null);
            onPriorityChange(null);
            onSenderChange(null);
            onStartDateChange(null);
            onEndDateChange(null);
          }}
          className="flex items-center gap-1 rounded-lg border border-border bg-background px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <X className="size-3" />
          Clear filters
        </button>
      )}
    </div>
  );
}