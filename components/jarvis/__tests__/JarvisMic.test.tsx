import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import "@testing-library/jest-dom/vitest";
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
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

interface FakeRecognitionInstance {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: unknown) => void) | null;
  onend: (() => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
  start: ReturnType<typeof vi.fn>;
  stop: ReturnType<typeof vi.fn>;
}

function installFakeRecognition() {
  const instances: FakeRecognitionInstance[] = [];
  class FakeRecognition implements FakeRecognitionInstance {
    lang = "";
    interimResults = false;
    continuous = false;
    onresult: ((event: unknown) => void) | null = null;
    onend: (() => void) | null = null;
    onerror: ((event: { error?: string }) => void) | null = null;
    start = vi.fn();
    stop = vi.fn();
    constructor() {
      instances.push(this);
    }
  }
  const descriptor = Object.getOwnPropertyDescriptor(
    window,
    "webkitSpeechRecognition"
  );
  Object.defineProperty(window, "webkitSpeechRecognition", {
    value: FakeRecognition,
    configurable: true,
    writable: true,
  });
  return {
    instances,
    restore() {
      if (descriptor) {
        Object.defineProperty(window, "webkitSpeechRecognition", descriptor);
      } else {
        delete (
          window as typeof window & { webkitSpeechRecognition?: unknown }
        ).webkitSpeechRecognition;
      }
    },
  };
}

function finalResultEvent(transcript: string) {
  return {
    resultIndex: 0,
    results: [{ isFinal: true, length: 1, 0: { transcript } }],
  };
}

describe("JarvisAssistant · speech-to-text", () => {
  let fake: ReturnType<typeof installFakeRecognition>;

  beforeEach(() => {
    vi.clearAllMocks();
    fake = installFakeRecognition();
  });

  afterEach(() => {
    fake.restore();
    cleanup();
  });

  it("puts recognized speech into the composer until the user sends it", async () => {
    const user = userEvent.setup();
    mocks.jarvisChat.mockResolvedValue({
      reply: "Hello Jarvis speaking.",
      action: null,
      used_ai: false,
    });

    render(<JarvisAssistant />);
    await user.click(screen.getByTestId("jarvis-launcher"));

    const mic = screen.getByRole("button", { name: "Talk to JARVIS" });
    expect(mic).toBeEnabled();
    await user.click(mic);

    act(() => {
      fake.instances[0].onresult?.(finalResultEvent("Hello Jarvis"));
    });

    const input = screen.getByLabelText("JARVIS command");
    expect(input).toHaveValue("Hello Jarvis");
    expect(mocks.jarvisChat).not.toHaveBeenCalled();

    await user.type(input, "{Enter}");
    await waitFor(() =>
      expect(mocks.jarvisChat).toHaveBeenCalledWith("Hello Jarvis")
    );
    expect(await screen.findByText("Hello Jarvis speaking.")).toBeInTheDocument();
    expect(input).toHaveValue("");
  });

  it("does not auto-send the transcript on its own", async () => {
    const user = userEvent.setup();
    render(<JarvisAssistant />);
    await user.click(screen.getByTestId("jarvis-launcher"));
    await user.click(screen.getByRole("button", { name: "Talk to JARVIS" }));

    act(() => {
      fake.instances[0].onresult?.(finalResultEvent("open my inbox"));
    });

    expect(screen.getByLabelText("JARVIS command")).toHaveValue("open my inbox");
    expect(mocks.jarvisChat).not.toHaveBeenCalled();
    expect(mocks.routerPush).not.toHaveBeenCalled();
  });
});