import { describe, it, expect, vi, afterEach } from "vitest";
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import JarvisPanel from "../JarvisPanel";

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

describe("JarvisPanel", () => {
  it("renders nothing when closed", () => {
    const { container } = render(
      <JarvisPanel
        {...baseProps}
        open={false}
        messages={[{ role: "assistant", text: "Hi" }]}
      />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the transcript", () => {
    render(
      <JarvisPanel
        {...baseProps}
        open
        messages={[
          { role: "user", text: "show inbox" },
          { role: "assistant", text: "Opening your inbox." },
        ]}
      />
    );
    expect(screen.getByText("show inbox")).toBeInTheDocument();
    expect(screen.getByText("Opening your inbox.")).toBeInTheDocument();
  });

  it("sends a non-empty draft on click", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(
      <JarvisPanel {...baseProps} open onSend={onSend} messages={[]} />
    );
    const input = screen.getByLabelText("Kestrel command");
    await user.type(input, "what needs my attention?");
    await user.click(screen.getByRole("button", { name: "Send command" }));
    expect(onSend).toHaveBeenCalledWith("what needs my attention?");
    expect(input).toHaveValue("");
  });

  it("sends on Enter and keeps send disabled for an empty draft", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<JarvisPanel {...baseProps} open onSend={onSend} messages={[]} />);
    const input = screen.getByLabelText("Kestrel command");
    expect(screen.getByRole("button", { name: "Send command" })).toBeDisabled();
    await user.type(input, "hello{Enter}");
    expect(onSend).toHaveBeenCalledWith("hello");
  });

  it("does not send while the assistant is busy", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(
      <JarvisPanel
        {...baseProps}
        open
        busy
        onSend={onSend}
        messages={[]}
      />
    );
    await user.click(screen.getByRole("button", { name: "Send command" }));
    expect(onSend).not.toHaveBeenCalled();
  });

  it("toggles the mic when supported", async () => {
    const user = userEvent.setup();
    const onToggleMic = vi.fn();
    render(<JarvisPanel {...baseProps} open onToggleMic={onToggleMic} messages={[]} />);
    await user.click(screen.getByRole("button", { name: "Talk to Kestrel" }));
    expect(onToggleMic).toHaveBeenCalledTimes(1);
  });

  it("disables the mic when the browser lacks SpeechRecognition", () => {
    render(
      <JarvisPanel {...baseProps} open micSupported={false} messages={[]} />
    );
    expect(screen.getByRole("button", { name: "Talk to Kestrel" })).toBeDisabled();
  });

  it("calls onClose from the header", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<JarvisPanel {...baseProps} open onClose={onClose} messages={[]} />);
    await user.click(screen.getByRole("button", { name: "Close Kestrel" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("reflects the state on the status pill", () => {
    render(
      <JarvisPanel
        {...baseProps}
        open
        state="listening"
        messages={[{ role: "user", text: "hi" }]}
      />
    );
    expect(screen.getByText("Listening…")).toBeInTheDocument();
    expect(within(screen.getByTestId("jarvis-panel")).getByRole("status")).toHaveAttribute(
      "data-state",
      "listening"
    );
  });
});