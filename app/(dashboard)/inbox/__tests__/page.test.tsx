import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import InboxPage from "../page";

vi.mock("@/lib/api", () => ({
  apiFetch: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(window.location.search),
}));

import { apiFetch } from "@/lib/api";

const mockMessages = [
  {
    id: "1",
    sender: "Ali",
    content: "Test message",
    source: "whatsapp",
    status: "unread",
    state: "active",
    ai_analysis: {
      priority: "urgent",
      confidence: 0.9,
      summary: "Test summary",
      recommended_action: "Test action",
      needs_attention: true,
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const mockCounts = {
  tabs: {
    all: 1,
    urgent: 1,
    important: 0,
    normal: 0,
    unread: 1,
  },
  sources: [{ name: "whatsapp", count: 1 }],
  priorities: [{ name: "urgent", count: 1 }],
};

describe("InboxPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiFetch).mockImplementation((url: string) => {
      if (url.includes("/messages/counts")) {
        return Promise.resolve(mockCounts);
      }
      if (url.startsWith("/messages")) {
        return Promise.resolve({ messages: mockMessages, total: 1 });
      }
      return Promise.reject(new Error("Unknown URL"));
    });
  });

  it("renders inbox page with title", async () => {
    render(<InboxPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Inbox").length).toBeGreaterThan(0);
      expect(screen.getAllByText(/message/).length).toBeGreaterThan(0);
    });
  });

  it("renders tab buttons", async () => {
    render(<InboxPage />);

    await waitFor(() => {
      expect(screen.getAllByText("All").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Urgent").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Important").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Normal").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Unread").length).toBeGreaterThan(0);
    });
  });

  it("displays messages after loading", async () => {
    render(<InboxPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Ali").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Test message").length).toBeGreaterThan(0);
    });
  });

  it("shows error state on API failure", async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error("API Error"));

    render(<InboxPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Failed to load messages. Please try again.").length).toBeGreaterThan(0);
    });
  });

  it("renders search bar", async () => {
    render(<InboxPage />);

    await waitFor(() => {
      expect(screen.getAllByPlaceholderText("Search messages...").length).toBeGreaterThan(0);
    });
  });

  it("renders filter buttons", async () => {
    render(<InboxPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Source").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Priority").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Sender").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Date Range").length).toBeGreaterThan(0);
    });
  });
});