import { describe, it, expect, vi } from "vitest";
import "@testing-library/jest-dom/vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import InboxTabs from "../InboxTabs";

const mockTabs = [
  { id: "all", label: "All", count: 10 },
  { id: "urgent", label: "Urgent", count: 2 },
  { id: "important", label: "Important", count: 3 },
  { id: "normal", label: "Normal", count: 5 },
  { id: "unread", label: "Unread", count: 1 },
];

describe("InboxTabs", () => {
  it("renders all tabs with counts", () => {
    const { container } = render(<InboxTabs tabs={mockTabs} activeTab="all" onTabChange={vi.fn()} />);
    const root = container.firstElementChild!;
    expect(within(root).getByText("All")).toBeDefined();
    expect(within(root).getByText("Urgent")).toBeDefined();
    expect(within(root).getByText("Important")).toBeDefined();
    expect(within(root).getByText("Normal")).toBeDefined();
    expect(within(root).getByText("Unread")).toBeDefined();
    expect(within(root).getByText("10")).toBeDefined();
    expect(within(root).getByText("2")).toBeDefined();
  });

  it("calls onTabChange when tab is clicked", async () => {
    const user = userEvent.setup();
    const onTabChange = vi.fn();
    const { container } = render(<InboxTabs tabs={mockTabs} activeTab="all" onTabChange={onTabChange} />);
    const root = container.firstElementChild!;

    const urgentBtn = within(root).getByRole("button", { name: /urgent/i });
    await user.click(urgentBtn);
    expect(onTabChange).toHaveBeenCalledWith("urgent");
  });

  it("highlights active tab", () => {
    const { container } = render(<InboxTabs tabs={mockTabs} activeTab="urgent" onTabChange={vi.fn()} />);
    const root = container.firstElementChild!;
    const urgentBtn = within(root).getByRole("button", { name: /urgent/i });
    expect(urgentBtn).toHaveClass("bg-background");
  });
});