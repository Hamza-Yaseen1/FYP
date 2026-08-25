import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import EmptyState from "../EmptyState";

describe("EmptyState", () => {
  it("renders no-messages state", () => {
    render(<EmptyState type="no-messages" />);

    expect(screen.getAllByText("No messages yet").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Your inbox is empty/).length).toBeGreaterThan(0);
  });

  it("renders no-results state with search query", () => {
    render(<EmptyState type="no-results" searchQuery="test query" />);

    expect(screen.getAllByText("No results found").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/No messages match "test query"/).length).toBeGreaterThan(0);
  });

  it("renders no-filtered-results state", () => {
    render(<EmptyState type="no-filtered-results" />);

    expect(screen.getAllByText("No messages match filters").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Try adjusting your filters/).length).toBeGreaterThan(0);
  });

  it("shows clear search button when onClearSearch is provided", () => {
    const onClearSearch = vi.fn();
    render(<EmptyState type="no-results" onClearSearch={onClearSearch} />);

    const clearButton = screen.getAllByText("Clear search")[0];
    expect(clearButton).toBeDefined();

    fireEvent.click(clearButton);
    expect(onClearSearch).toHaveBeenCalled();
  });

  it("shows clear filters button when onClearFilters is provided", () => {
    const onClearFilters = vi.fn();
    render(<EmptyState type="no-filtered-results" onClearFilters={onClearFilters} />);

    const clearButton = screen.getAllByText("Clear all filters")[0];
    expect(clearButton).toBeDefined();

    fireEvent.click(clearButton);
    expect(onClearFilters).toHaveBeenCalled();
  });
});