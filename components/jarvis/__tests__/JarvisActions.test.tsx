import { describe, it, expect, vi, afterEach } from "vitest";
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import JarvisPanel from "../JarvisPanel";
import type { JarvisMessage } from "../types";

afterEach(cleanup);

const baseProps = {
  state: "idle" as const,
  messages: [],
  micSupported: true,
  listening: false,
  busy: false,
  onSend: vi.fn(),
  onToggleMic: vi.fn(),
  onClose: vi.fn(),
};

const confirmationMessage: JarvisMessage = {
  role: "assistant",
  text: "Should I create it?",
  action: {
    type: "request_confirmation",
    confirmation_token: "tok-123",
    detail: {
      pending_type: "create_task",
      summary: "Create task: finish docs\nDue: friday\nPriority: important",
    },
  },
};

const draftMessage: JarvisMessage = {
  role: "assistant",
  text: "Reply preview.",
  action: {
    type: "draft_reply",
    detail: { draft: "Dear Ali,\n\nI will send it tomorrow.\n\nBest regards" },
  },
};

describe("JarvisPanel · Phase 2 actions", () => {
  it("shows the pending summary with Confirm and Cancel buttons", () => {
    render(
      <JarvisPanel
        {...baseProps}
        open
        messages={[confirmationMessage]}
      />
    );
    expect(screen.getByTestId("jarvis-pending-summary")).toHaveTextContent(
      "Create task: finish docs"
    );
    expect(screen.getByTestId("jarvis-pending-summary")).toHaveTextContent(
      "Due: friday"
    );
    expect(
      screen.getByRole("button", { name: "Confirm JARVIS action" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Cancel JARVIS action" })
    ).toBeInTheDocument();
  });

  it("calls onConfirm with the pending message", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    render(
      <JarvisPanel {...baseProps} open onConfirm={onConfirm} messages={[confirmationMessage]} />
    );
    await user.click(
      screen.getByRole("button", { name: "Confirm JARVIS action" })
    );
    expect(onConfirm).toHaveBeenCalledWith(confirmationMessage);
  });

  it("calls onCancel with the pending message", async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(
      <JarvisPanel {...baseProps} open onCancel={onCancel} messages={[confirmationMessage]} />
    );
    await user.click(
      screen.getByRole("button", { name: "Cancel JARVIS action" })
    );
    expect(onCancel).toHaveBeenCalledWith(confirmationMessage);
  });

  it("disables the action buttons while confirming", () => {
    render(
      <JarvisPanel {...baseProps} open confirming messages={[confirmationMessage]} />
    );
    expect(
      screen.getByRole("button", { name: "Confirm JARVIS action" })
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Cancel JARVIS action" })
    ).toBeDisabled();
  });

  it("renders the draft block with a not-sent marker", () => {
    render(<JarvisPanel {...baseProps} open messages={[draftMessage]} />);
    const block = screen.getByTestId("jarvis-draft-block");
    expect(block).toHaveTextContent("Draft · not sent");
    expect(block).toHaveTextContent("Dear Ali,");
    expect(block).toHaveTextContent("I will send it tomorrow.");
  });

  it("locks the composer while a confirmation is pending", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(
      <JarvisPanel
        {...baseProps}
        open
        pendingConfirmation
        onSend={onSend}
        messages={[confirmationMessage]}
      />
    );
    const input = screen.getByLabelText("JARVIS command");
    expect(input).toBeDisabled();
    expect(input).toHaveAttribute(
      "placeholder",
      "Confirm or cancel your pending action…"
    );
    expect(screen.getByRole("button", { name: "Send command" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Talk to JARVIS" })).toBeDisabled();

    await user.type(input, "stop");
    expect(onSend).not.toHaveBeenCalled();
  });
});