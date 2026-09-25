import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { JarvisChatResponse } from "@/lib/api/jarvis";

const mocks = vi.hoisted(() => ({
  jarvisChat: vi.fn<() => Promise<JarvisChatResponse>>(),
  routerPush: vi.fn(),
}));

vi.mock("@/lib/api/jarvis", () => ({ jarvisChat: mocks.jarvisChat }));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mocks.routerPush }),
}));

import JarvisAssistant from "../JarvisAssistant";

afterEach(cleanup);

const confirmationReply: JarvisChatResponse = {
  reply: "Should I create it?",
  action: {
    type: "request_confirmation",
    confirmation_token: "tok-123",
    detail: { pending_type: "create_task", summary: "Create task: finish docs" },
  },
  used_ai: false,
};

const confirmExecuted: JarvisChatResponse = {
  reply: "Done. I've created the task \"finish docs\".",
  action: { type: "create_task", detail: { task_id: "abc", title: "finish docs" } },
  used_ai: false,
};

const cancelResult: JarvisChatResponse = {
  reply: "Understood — I have not made any changes.",
  action: null,
  used_ai: false,
};

describe("JarvisAssistant · confirmation flow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("requests confirmation and locks the composer until resolved", async () => {
    const user = userEvent.setup();
    mocks.jarvisChat.mockResolvedValue(confirmationReply);
    render(<JarvisAssistant />);
    await user.click(screen.getByTestId("jarvis-launcher"));

    await user.type(
      screen.getByLabelText("JARVIS command"),
      "create a task called finish docs{Enter}"
    );

    expect(await screen.findByText("Should I create it?")).toBeInTheDocument();
    expect(screen.getByTestId("jarvis-pending-summary")).toHaveTextContent(
      "Create task: finish docs"
    );
    const input = screen.getByLabelText("JARVIS command");
    expect(input).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Confirm JARVIS action" })
    ).toBeInTheDocument();
    expect(mocks.routerPush).not.toHaveBeenCalled();
  });

  it("round-trips the token on confirm and unlocks the composer", async () => {
    const user = userEvent.setup();
    mocks.jarvisChat
      .mockResolvedValueOnce(confirmationReply)
      .mockResolvedValueOnce(confirmExecuted);
    render(<JarvisAssistant />);
    await user.click(screen.getByTestId("jarvis-launcher"));

    await user.type(
      screen.getByLabelText("JARVIS command"),
      "create a task called finish docs{Enter}"
    );
    await screen.findByText("Should I create it?");

    await user.click(
      screen.getByRole("button", { name: "Confirm JARVIS action" })
    );

    expect(
      await screen.findByText("Done. I've created the task \"finish docs\".")
    ).toBeInTheDocument();
    expect(mocks.jarvisChat).toHaveBeenLastCalledWith("", {
      confirmation_token: "tok-123",
      confirmed: true,
    });
    await waitFor(() => {
      expect(screen.getByLabelText("JARVIS command")).toBeEnabled();
    });
  });

  it("cancels without executing and unlocks the composer", async () => {
    const user = userEvent.setup();
    mocks.jarvisChat
      .mockResolvedValueOnce(confirmationReply)
      .mockResolvedValueOnce(cancelResult);
    render(<JarvisAssistant />);
    await user.click(screen.getByTestId("jarvis-launcher"));

    await user.type(
      screen.getByLabelText("JARVIS command"),
      "create a task called finish docs{Enter}"
    );
    await screen.findByText("Should I create it?");

    await user.click(
      screen.getByRole("button", { name: "Cancel JARVIS action" })
    );

    expect(
      await screen.findByText("Understood — I have not made any changes.")
    ).toBeInTheDocument();
    expect(mocks.jarvisChat).toHaveBeenLastCalledWith("", {
      confirmation_token: "tok-123",
      confirmed: false,
    });
    await waitFor(() => {
      expect(screen.getByLabelText("JARVIS command")).toBeEnabled();
    });
  });

  it("recovers with the fallback message when the confirm call fails", async () => {
    const user = userEvent.setup();
    mocks.jarvisChat
      .mockResolvedValueOnce(confirmationReply)
      .mockRejectedValueOnce(new Error("boom"));
    render(<JarvisAssistant />);
    await user.click(screen.getByTestId("jarvis-launcher"));

    await user.type(
      screen.getByLabelText("JARVIS command"),
      "create a task called finish docs{Enter}"
    );
    await screen.findByText("Should I create it?");

    await user.click(
      screen.getByRole("button", { name: "Confirm JARVIS action" })
    );

    expect(
      await screen.findByText(
        "Sorry, I could not reach the server. Please try again."
      )
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByLabelText("JARVIS command")).toBeEnabled();
    });
  });

  it("navigates when a confirm round-trip returns a navigation action", async () => {
    const user = userEvent.setup();
    const navigateReply: JarvisChatResponse = {
      reply: "Opening your inbox.",
      action: { type: "navigation", target: "/inbox" },
      used_ai: false,
    };
    mocks.jarvisChat
      .mockResolvedValueOnce(confirmationReply)
      .mockResolvedValueOnce(navigateReply);
    render(<JarvisAssistant />);
    await user.click(screen.getByTestId("jarvis-launcher"));

    await user.type(
      screen.getByLabelText("JARVIS command"),
      "create a task called finish docs{Enter}"
    );
    await screen.findByText("Should I create it?");

    await user.click(
      screen.getByRole("button", { name: "Confirm JARVIS action" })
    );

    expect(await screen.findByText("Opening your inbox.")).toBeInTheDocument();
    expect(mocks.routerPush).toHaveBeenCalledWith("/inbox");
  });
});