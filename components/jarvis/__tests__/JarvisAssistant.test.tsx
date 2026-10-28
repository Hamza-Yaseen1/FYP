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

const navigationReply: JarvisChatResponse = {
  reply: "Opening your inbox.",
  action: { type: "navigation", target: "/inbox" },
  used_ai: false,
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("JarvisAssistant", () => {
  it("opens from the launcher", async () => {
    const user = userEvent.setup();
    render(<JarvisAssistant />);
    expect(screen.queryByTestId("jarvis-panel")).not.toBeInTheDocument();
    await user.click(screen.getByTestId("jarvis-launcher"));
    expect(screen.getByTestId("jarvis-panel")).toBeInTheDocument();
  });

  it("sends a typed command, renders the reply and navigates", async () => {
    const user = userEvent.setup();
    mocks.jarvisChat.mockResolvedValue(navigationReply);
    render(<JarvisAssistant />);
    await user.click(screen.getByTestId("jarvis-launcher"));

    await user.type(
      screen.getByLabelText("Kestrel command"),
      "take me to inbox{Enter}"
    );

    await waitFor(() =>
      expect(mocks.jarvisChat).toHaveBeenCalledWith("take me to inbox")
    );
    expect(await screen.findByText("Opening your inbox.")).toBeInTheDocument();
    expect(mocks.routerPush).toHaveBeenCalledWith("/inbox");
  });

  it("localizes legacy assistant and product names in replies", async () => {
    const user = userEvent.setup();
    mocks.jarvisChat.mockResolvedValue({
      reply: "I am JARVIS, your Signal Desk assistant.",
      action: null,
      used_ai: false,
    });
    render(<JarvisAssistant />);
    await user.click(screen.getByTestId("jarvis-launcher"));

    await user.type(
      screen.getByLabelText("Kestrel command"),
      "who are you{Enter}"
    );

    expect(
      await screen.findByText("I am Kestrel, your Sift assistant.")
    ).toBeInTheDocument();
  });

  it("shows a fallback message on backend failure", async () => {
    const user = userEvent.setup();
    mocks.jarvisChat.mockRejectedValue(new Error("boom"));
    render(<JarvisAssistant />);
    await user.click(screen.getByTestId("jarvis-launcher"));
    await user.type(screen.getByLabelText("Kestrel command"), "unread{Enter}");

    expect(
      await screen.findByText(
        "Sorry, I could not reach the server. Please try again."
      )
    ).toBeInTheDocument();
    expect(mocks.routerPush).not.toHaveBeenCalled();
  });

  it("does not call the backend for empty input", async () => {
    const user = userEvent.setup();
    render(<JarvisAssistant />);
    await user.click(screen.getByTestId("jarvis-launcher"));
    await user.type(screen.getByLabelText("Kestrel command"), "   {Enter}");
    expect(mocks.jarvisChat).not.toHaveBeenCalled();
  });

  it("closes the panel and stays usable again", async () => {
    const user = userEvent.setup();
    render(<JarvisAssistant />);
    await user.click(screen.getByTestId("jarvis-launcher"));
    await user.click(screen.getByRole("button", { name: "Close Kestrel" }));
    expect(screen.queryByTestId("jarvis-panel")).not.toBeInTheDocument();
    expect(screen.getByTestId("jarvis-launcher")).toBeInTheDocument();
  });
});