"use client";

import { Inbox, Search, Filter } from "lucide-react";

interface EmptyStateProps {
  type: "no-messages" | "no-results" | "no-filtered-results";
  searchQuery?: string;
  onClearSearch?: () => void;
  onClearFilters?: () => void;
  className?: string;
}

export default function EmptyState({
  type,
  searchQuery,
  onClearSearch,
  onClearFilters,
  className,
}: EmptyStateProps) {
  const configs = {
    "no-messages": {
      icon: Inbox,
      title: "No messages yet",
      description: "Your inbox is empty. Messages will appear here when they arrive.",
      action: null,
    },
    "no-results": {
      icon: Search,
      title: "No results found",
      description: searchQuery
        ? `No messages match "${searchQuery}"`
        : "No messages match your search.",
      action: onClearSearch
        ? { label: "Clear search", onClick: onClearSearch }
        : null,
    },
    "no-filtered-results": {
      icon: Filter,
      title: "No messages match filters",
      description: "Try adjusting your filters or search criteria.",
      action: onClearFilters
        ? { label: "Clear all filters", onClick: onClearFilters }
        : null,
    },
  };

  const config = configs[type];
  const Icon = config.icon;

  return (
    <div className={`flex flex-col items-center justify-center rounded-xl border border-dashed py-16 ${className ?? ""}`}>
      <Icon className="size-10 text-muted-foreground/50" />
      <h3 className="mt-4 text-sm font-medium text-foreground">{config.title}</h3>
      <p className="mt-1 text-sm text-muted-foreground">{config.description}</p>
      {config.action && (
        <button
          onClick={config.action.onClick}
          className="mt-4 text-sm font-medium text-primary hover:underline"
        >
          {config.action.label}
        </button>
      )}
    </div>
  );
}