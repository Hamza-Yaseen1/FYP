import { describe, it, expect, vi } from "vitest";
import "@testing-library/jest-dom/vitest";
import { render, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import FilterBar from "../FilterBar";

const mockProps = {
  sources: [{ value: "whatsapp", label: "WhatsApp" }, { value: "gmail", label: "Gmail" }],
  priorities: [{ value: "urgent", label: "Urgent" }, { value: "normal", label: "Normal" }],
  senders: [{ value: "Ali", label: "Ali" }, { value: "Sara", label: "Sara" }],
  selectedSource: null,
  selectedPriority: null,
  selectedSender: null,
  startDate: null,
  endDate: null,
  onSourceChange: vi.fn(),
  onPriorityChange: vi.fn(),
  onSenderChange: vi.fn(),
  onStartDateChange: vi.fn(),
  onEndDateChange: vi.fn(),
};

describe("FilterBar", () => {
  it("renders filter buttons", () => {
    const { container } = render(<FilterBar {...mockProps} />);
    const root = container.firstElementChild!;
    expect(within(root).getByText("Source")).toBeDefined();
    expect(within(root).getByText("Priority")).toBeDefined();
    expect(within(root).getByText("Sender")).toBeDefined();
    expect(within(root).getByText("Date Range")).toBeDefined();
  });

  it("opens source dropdown and calls onSourceChange when option is selected", async () => {
    const user = userEvent.setup();
    const onSourceChange = vi.fn();
    const { container } = render(<FilterBar {...mockProps} onSourceChange={onSourceChange} />);
    const root = container.firstElementChild!;

    await user.click(within(root).getByRole("button", { name: /source/i }));
    await user.click(within(root).getByRole("button", { name: "WhatsApp" }));
    expect(onSourceChange).toHaveBeenCalledWith("whatsapp");
  });

  it("opens priority dropdown and calls onPriorityChange", async () => {
    const user = userEvent.setup();
    const onPriorityChange = vi.fn();
    const { container } = render(<FilterBar {...mockProps} onPriorityChange={onPriorityChange} />);
    const root = container.firstElementChild!;

    await user.click(within(root).getByRole("button", { name: /priority/i }));
    await user.click(within(root).getByRole("button", { name: "Urgent" }));
    expect(onPriorityChange).toHaveBeenCalledWith("urgent");
  });

  it("shows clear filters button when filters are active", () => {
    const { container } = render(<FilterBar {...mockProps} selectedSource="whatsapp" />);
    const root = container.firstElementChild!;
    expect(within(root).getByText("Clear filters")).toBeDefined();
  });

  it("calls all clear functions when clear button is clicked", async () => {
    const user = userEvent.setup();
    const onSourceChange = vi.fn();
    const onPriorityChange = vi.fn();
    const onSenderChange = vi.fn();
    const onStartDateChange = vi.fn();
    const onEndDateChange = vi.fn();

    const { container } = render(
      <FilterBar
        {...mockProps}
        selectedSource="whatsapp"
        onSourceChange={onSourceChange}
        onPriorityChange={onPriorityChange}
        onSenderChange={onSenderChange}
        onStartDateChange={onStartDateChange}
        onEndDateChange={onEndDateChange}
      />
    );
    const root = container.firstElementChild!;

    await user.click(within(root).getByRole("button", { name: /clear filters/i }));
    expect(onSourceChange).toHaveBeenCalledWith(null);
    expect(onPriorityChange).toHaveBeenCalledWith(null);
    expect(onSenderChange).toHaveBeenCalledWith(null);
    expect(onStartDateChange).toHaveBeenCalledWith(null);
    expect(onEndDateChange).toHaveBeenCalledWith(null);
  });
});