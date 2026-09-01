"use client";

import { useState } from "react";
import { ChevronDown, X, Calendar } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

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

const triggerBase =
  "flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors";
const triggerIdle =
  "border-border bg-card text-muted-foreground hover:text-foreground";
const triggerActive =
  "border-primary/40 bg-primary/10 text-primary";

const panelBase =
  "absolute left-0 top-full z-10 mt-1.5 w-44 overflow-hidden rounded-lg border border-border bg-card p-1 shadow-md";

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

  const renderOptions = (
    options: FilterOption[],
    selected: string | null,
    allLabel: string,
    onSelect: (value: string | null) => void
  ) => (
    <div className={panelBase}>
      <button
        onClick={() => {
          onSelect(null);
          setOpenDropdown(null);
        }}
        className={cn(
          "w-full rounded-md px-3 py-1.5 text-left text-sm transition-colors hover:bg-muted",
          !selected && "bg-accent font-medium"
        )}
      >
        {allLabel}
      </button>
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => {
            onSelect(option.value);
            setOpenDropdown(null);
          }}
          className={cn(
            "w-full rounded-md px-3 py-1.5 text-left text-sm transition-colors hover:bg-muted",
            selected === option.value && "bg-accent font-medium"
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );

  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      {/* Source Filter */}
      <div className="relative">
        <button
          onClick={() => setOpenDropdown(openDropdown === "source" ? null : "source")}
          className={cn(triggerBase, selectedSource ? triggerActive : triggerIdle)}
        >
          Source
          <ChevronDown className="size-3" />
        </button>
        {openDropdown === "source" &&
          renderOptions(sources, selectedSource, "All sources", onSourceChange)}
      </div>

      {/* Priority Filter */}
      <div className="relative">
        <button
          onClick={() => setOpenDropdown(openDropdown === "priority" ? null : "priority")}
          className={cn(triggerBase, selectedPriority ? triggerActive : triggerIdle)}
        >
          Priority
          <ChevronDown className="size-3" />
        </button>
        {openDropdown === "priority" &&
          renderOptions(priorities, selectedPriority, "All priorities", onPriorityChange)}
      </div>

      {/* Sender Filter */}
      <div className="relative">
        <button
          onClick={() => setOpenDropdown(openDropdown === "sender" ? null : "sender")}
          className={cn(triggerBase, selectedSender ? triggerActive : triggerIdle)}
        >
          Sender
          <ChevronDown className="size-3" />
        </button>
        {openDropdown === "sender" &&
          renderOptions(senders, selectedSender, "All senders", onSenderChange)}
      </div>

      {/* Date Range Filter */}
      <div className="relative">
        <button
          onClick={() => setShowDateRange(!showDateRange)}
          className={cn(triggerBase, startDate || endDate ? triggerActive : triggerIdle)}
        >
          <Calendar className="size-3" />
          Date Range
        </button>
        {showDateRange && (
          <div className="absolute left-0 top-full z-10 mt-1.5 w-64 rounded-lg border border-border bg-card p-3 shadow-md">
            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">From</label>
                <input
                  type="date"
                  value={startDate || ""}
                  onChange={(e) => onStartDateChange(e.target.value || null)}
                  className="h-8 w-full rounded-md border border-input bg-transparent px-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">To</label>
                <input
                  type="date"
                  value={endDate || ""}
                  onChange={(e) => onEndDateChange(e.target.value || null)}
                  className="h-8 w-full rounded-md border border-input bg-transparent px-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                />
              </div>
              <Button
                size="sm"
                onClick={() => setShowDateRange(false)}
                className="w-full"
              >
                Apply
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Clear Filters */}
      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            onSourceChange(null);
            onPriorityChange(null);
            onSenderChange(null);
            onStartDateChange(null);
            onEndDateChange(null);
          }}
        >
          <X className="size-3" />
          Clear filters
        </Button>
      )}
    </div>
  );
}