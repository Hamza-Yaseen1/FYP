import { describe, it, expect } from "vitest";
import "@testing-library/jest-dom/vitest";
import { render, within } from "@testing-library/react";
import { act } from "react";
import PriorityBadge from "../PriorityBadge";

const baseProps = {
  messageId: "msg-1",
  priority: "normal",
};

describe("PriorityBadge", () => {
  it("shows only a Pending badge (no confidence, no flags) when status is pending", () => {
    const { container } = render(
      <PriorityBadge {...baseProps} status="pending" confidence={0} />
    );
    const root = container.firstElementChild as HTMLElement;
    expect(within(root).getByText("Pending")).toBeDefined();
    expect(within(root).queryByText(/%/)).toBeNull();
    expect(within(root).queryByText(/review/i)).toBeNull();
    expect(within(root).queryByText(/verify/i)).toBeNull();
  });

  it("shows Urgent + confidence, no flags, for a completed high-confidence analysis", () => {
    const { container } = render(
      <PriorityBadge
        {...baseProps}
        priority="urgent"
        status="completed"
        confidence={0.95}
      />
    );
    const root = container.firstElementChild as HTMLElement;
    expect(within(root).getByText("Urgent")).toBeDefined();
    expect(within(root).getByText("95%")).toBeDefined();
    expect(within(root).queryByText(/review/i)).toBeNull();
    expect(within(root).queryByText(/verify/i)).toBeNull();
  });

  it("shows a Review flag for completed low-confidence analyses", () => {
    const { container } = render(
      <PriorityBadge
        {...baseProps}
        priority="normal"
        status="completed"
        confidence={0.4}
      />
    );
    const root = container.firstElementChild as HTMLElement;
    expect(within(root).getByText("Normal")).toBeDefined();
    expect(within(root).getByText("40%")).toBeDefined();
    expect(within(root).getByText("Review")).toBeDefined();
  });

  it("shows a Verify flag for mid-confidence analyses", () => {
    const { container } = render(
      <PriorityBadge
        {...baseProps}
        priority="important"
        status="completed"
        confidence={0.6}
      />
    );
    const root = container.firstElementChild as HTMLElement;
    expect(within(root).getByText("Important")).toBeDefined();
    expect(within(root).getByText("60%")).toBeDefined();
    expect(within(root).getByText("Verify")).toBeDefined();
    expect(within(root).queryByText(/review/i)).toBeNull();
  });

  it("updates the label when the priority prop changes after re-analysis", async () => {
    const view = render(
      <PriorityBadge {...baseProps} priority="normal" status="completed" confidence={0.9} />
    );
    expect(view.container.textContent).toContain("Normal");

    await act(async () => {
      view.rerender(
        <PriorityBadge
          {...baseProps}
          priority="urgent"
          status="completed"
          confidence={0.9}
        />
      );
    });

    expect(view.container.textContent).toContain("Urgent");
    expect(view.container.textContent).not.toContain("Normal");
  });
});