import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent, cleanup } from "@testing-library/react";
import AnalyticsPage from "../page";
import type { AnalyticsResponse } from "@/lib/api/analytics";

vi.mock("@/lib/api", () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from "@/lib/api";

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
vi.stubGlobal("ResizeObserver", ResizeObserverStub);

const makeResponse = (
  overrides: Partial<AnalyticsResponse> = {}
): AnalyticsResponse => ({
  period: "week",
  from: "2026-09-04T00:00:00Z",
  to: "2026-09-11T23:59:59Z",
  total: 5,
  by_priority: { urgent: 1, important: 1, normal: 2, low: 1, pending: 0 },
  by_source: { whatsapp: 3, gmail: 2 },
  tasks: { total: 2, completed: 1 },
  trends: [],
  ...overrides,
});

describe("AnalyticsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("fetches with default period week and renders overview", async () => {
    vi.mocked(apiFetch).mockResolvedValue(makeResponse());

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith("/analytics?period=week");
      expect(screen.getAllByText("Communication Overview").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Total Communications").length).toBeGreaterThan(0);
    });
    expect(screen.getAllByText("5").length).toBeGreaterThan(0);
  });

  it("shows the empty state when there is no data", async () => {
    vi.mocked(apiFetch).mockResolvedValue(
      makeResponse({ total: 0, by_priority: { urgent: 0, important: 0, normal: 0, low: 0, pending: 0 }, by_source: {} })
    );

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getAllByText("No data yet").length).toBeGreaterThan(0);
    });
  });

  it("shows the error state on API failure", async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error("API Error"));

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(
        screen.getAllByText("Could not load analytics data.").length
      ).toBeGreaterThan(0);
    });
  });

  it("does not render content while the request is pending", async () => {
    vi.mocked(apiFetch).mockImplementation(() => new Promise(() => {}));

    render(<AnalyticsPage />);

    expect(screen.queryByText("Total Communications")).toBeNull();
  });

  it("refetches with the new period when the toggle is changed", async () => {
    vi.mocked(apiFetch)
      .mockResolvedValueOnce(makeResponse())
      .mockResolvedValueOnce(makeResponse({ period: "day", total: 2 }));

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Total Communications").length).toBeGreaterThan(0);
    });

    fireEvent.click(screen.getAllByText("Today")[0]);

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith("/analytics?period=day");
      expect(screen.getAllByText("2").length).toBeGreaterThan(0);
    });
  });
});