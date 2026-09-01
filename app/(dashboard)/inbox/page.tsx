"use client";

import { useState, useEffect } from "react";
import InboxTabs from "@/components/InboxTabs";
import FilterBar from "@/components/FilterBar";
import SearchBar from "@/components/SearchBar";
import EmptyState from "@/components/EmptyState";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import PriorityBadge from "@/components/PriorityBadge";
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
    summary?: string;
    explanation?: string;
    recommended_action?: string;
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
  updated_at: string;
}

interface FilterCounts {
  tabs: {
    all: number;
    urgent: number;
    important: number;
    normal: number;
    unread: number;
  };
  sources: Record<string, number>; // Changed from Array to Record
  priorities: Record<string, number>; // Changed from Array to Record
}

interface SendersResponse {
  senders: Array<{ name: string; count: number }>;
}

const TABS = [
  { id: "all", label: "All" },
  { id: "urgent", label: "Urgent" },
  { id: "important", label: "Important" },
  { id: "normal", label: "Normal" },
  { id: "unread", label: "Unread" },
];

export default function InboxPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("all");
  const [counts, setCounts] = useState<FilterCounts | null>(null);
  const [senders, setSenders] = useState<Array<{ name: string; count: number }>>([]);
  const [total, setTotal] = useState(0);
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [selectedPriority, setSelectedPriority] = useState<string | null>(null);
  const [selectedSender, setSelectedSender] = useState<string | null>(null);
  const [startDate, setStartDate] = useState<string | null>(null);
  const [endDate, setEndDate] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (activeTab !== "all") params.set("tab", activeTab);
        if (selectedSource) params.set("source", selectedSource);
        if (selectedPriority) params.set("priority", selectedPriority);
        if (selectedSender) params.set("sender", selectedSender);
        if (startDate) params.set("start_date", startDate);
        if (endDate) params.set("end_date", endDate);
        if (searchQuery) params.set("search", searchQuery);
        const url = `/messages${params.toString() ? `?${params.toString()}` : ""}`;
        const data = await apiFetch<{ messages: Message[]; total: number }>(url);
        if (!cancelled) {
          setMessages(data.messages);
          setTotal(data.total);
        }
      } catch (err) {
        console.error("Failed to fetch messages:", err);
        if (!cancelled) setError("Failed to load messages. Please try again.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();

    apiFetch<FilterCounts>("/messages/counts")
      .then((data) => { if (!cancelled) setCounts(data); })
      .catch((err) => console.error("Failed to fetch counts:", err));

    apiFetch<SendersResponse>("/messages/senders")
      .then((data) => { if (!cancelled) setSenders(data.senders || []); })
      .catch((err) => console.error("Failed to fetch senders:", err));

    return () => { cancelled = true; };
  }, [activeTab, selectedSource, selectedPriority, selectedSender, startDate, endDate, searchQuery, refreshKey]);

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
  };

  const handleSourceChange = (source: string | null) => {
    setSelectedSource(source);
  };

  const handlePriorityChange = (priority: string | null) => {
    setSelectedPriority(priority);
  };

  const handleSenderChange = (sender: string | null) => {
    setSelectedSender(sender);
  };

  const handleStartDateChange = (date: string | null) => {
    setStartDate(date);
  };

  const handleEndDateChange = (date: string | null) => {
    setEndDate(date);
  };

  const handleSearchChange = (query: string) => {
    setSearchQuery(query);
  };

  const handleClearSearch = () => {
    setSearchQuery("");
  };

  const handleClearAllFilters = () => {
    setActiveTab("all");
    setSelectedSource(null);
    setSelectedPriority(null);
    setSelectedSender(null);
    setStartDate(null);
    setEndDate(null);
    setSearchQuery("");
  };

  const tabsWithCounts = TABS.map((tab) => ({
    ...tab,
    count: counts?.tabs[tab.id as keyof FilterCounts["tabs"]],
  }));

  const sourceOptions = Object.entries(counts?.sources || {}).map(([name, count]) => ({
    value: name,
    label: `${name} (${count})`,
  }));

  const priorityOptions = Object.entries(counts?.priorities || {}).map(([name, count]) => ({
    value: name,
    label: `${name} (${count})`,
  }));

  const senderOptions = senders.map((s) => ({
    value: s.name,
    label: `${s.name} (${s.count})`,
  }));

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Inbox</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {total} message{total !== 1 ? "s" : ""} in
          </p>
        </div>
      </div>

      <div className="mt-6">
        <InboxTabs
          tabs={tabsWithCounts}
          activeTab={activeTab}
          onTabChange={handleTabChange}
        />
      </div>

      <div className="mt-4">
        <FilterBar
          sources={sourceOptions}
          priorities={priorityOptions}
          senders={senderOptions}
          selectedSource={selectedSource}
          selectedPriority={selectedPriority}
          selectedSender={selectedSender}
          startDate={startDate}
          endDate={endDate}
          onSourceChange={handleSourceChange}
          onPriorityChange={handlePriorityChange}
          onSenderChange={handleSenderChange}
          onStartDateChange={handleStartDateChange}
          onEndDateChange={handleEndDateChange}
        />
      </div>

      <div className="mt-4">
        <SearchBar
          value={searchQuery}
          onChange={handleSearchChange}
          onClear={handleClearSearch}
          placeholder="Search messages..."
        />
      </div>

      <div className="mt-6">
        {loading ? (
          <LoadingSkeleton count={3} />
        ) : error ? (
          <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-6 text-center">
            <p className="text-sm text-destructive">{error}</p>
            <button
              onClick={() => setRefreshKey((k) => k + 1)}
              className="mt-2 text-sm font-medium text-destructive hover:underline"
            >
              Try again
            </button>
          </div>
        ) : messages.length === 0 ? (
          <EmptyState
            type={activeTab === "all" && !selectedSource && !selectedPriority && !selectedSender && !startDate && !endDate && !searchQuery ? "no-messages" : searchQuery ? "no-results" : "no-filtered-results"}
            searchQuery={searchQuery}
            onClearSearch={handleClearSearch}
            onClearFilters={handleClearAllFilters}
          />
        ) : (
          <div className="space-y-2.5">
            {messages.map((msg) => (
              <MessageCard key={msg.id} message={msg} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function MessageCard({ message: msg }: { message: Message }) {
  const analysis = msg.ai_analysis;
  const timeAgo = getTimeAgo(msg.created_at);
  const confidence = analysis?.confidence ? Math.round(analysis.confidence * 100) : null;

  return (
    <article className="rounded-xl border border-border bg-card p-4 transition-colors hover:border-muted-foreground/25">
      <div className="flex items-start gap-3">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold text-muted-foreground">
          {msg.sender.charAt(0).toUpperCase()}
        </div>
        <div className="min-w-0 flex-1">
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
            {confidence !== null && (
              <span className="font-mono text-[10px] text-muted-foreground">
                {confidence}% confidence
              </span>
            )}
          </div>
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
          <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-foreground/90">
            {msg.content}
          </p>
          {analysis?.summary && (
            <div className="mt-2 rounded-lg bg-muted/60 p-2.5">
              <p className="triage-label text-muted-foreground/70">Summary</p>
              <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                {analysis.summary}
              </p>
            </div>
          )}
          {analysis?.recommended_action && (
            <div className="mt-2 rounded-lg bg-muted/60 p-2.5">
              <p className="triage-label text-primary">Move on</p>
              <p className="mt-1 text-xs leading-relaxed text-foreground/90">
                {analysis.recommended_action}
              </p>
            </div>
          )}
        </div>
        <div className="shrink-0 font-mono text-[11px] text-muted-foreground">{timeAgo}</div>
      </div>
    </article>
  );
}

function getTimeAgo(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return date.toLocaleDateString();
}
