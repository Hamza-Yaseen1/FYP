import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import "@testing-library/jest-dom/vitest";
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { JarvisChatResponse } from "@/lib/api/jarvis";

const mocks = vi.hoisted(() => ({
  jarvisChat: vi.fn<() => Promise<JarvisChatResponse>>(),
  routerPush: vi.fn(),
  synthCancel: vi.fn(),
  synthSpeak: vi.fn(),
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

interface FakeUtterance {
  text: string;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: ((event: unknown) => void) | null;
}

function installFakeSpeech() {
  const utterances: FakeUtterance[] = [];
  class FakeUtteranceImpl implements FakeUtterance {
    text: string;
    onstart: (() => void) | null = null;
    onend: (() => void) | null = null;
    onerror: ((event: unknown) => void) | null = null;
    constructor(text: string) {
      this.text = text;
      utterances.push(this);
    }
  }
  const synthDescriptor = Object.getOwnPropertyDescriptor(
    window,
    "speechSynthesis"
  );
  Object.defineProperty(window, "speechSynthesis", {
    value: {
      speak: mocks.synthSpeak,
      cancel: mocks.synthCancel,
    },
    configurable: true,
    writable: true,
  });
  const utteranceDescriptor = Object.getOwnPropertyDescriptor(
    globalThis,
    "SpeechSynthesisUtterance"
  );
  Object.defineProperty(globalThis, "SpeechSynthesisUtterance", {
    value: FakeUtteranceImpl,
    configurable: true,
    writable: true,
  });
  Object.defineProperty(window, "SpeechSynthesisUtterance", {
    value: FakeUtteranceImpl,
    configurable: true,
    writable: true,
  });
  return {
    utterances,
    restore() {
      const w = window as unknown as Record<string, unknown>;
      if (synthDescriptor) {
        Object.defineProperty(window, "speechSynthesis", synthDescriptor);
      } else {
        delete w.speechSynthesis;
      }
      const g = globalThis as unknown as Record<string, unknown>;
      if (utteranceDescriptor) {
        Object.defineProperty(
          globalThis,
          "SpeechSynthesisUtterance",
          utteranceDescriptor
        );
      } else {
        delete g.SpeechSynthesisUtterance;
      }
      delete w.SpeechSynthesisUtterance;
    },
  };
}

function interimEvent(text: string) {
  return {
    resultIndex: 0,
    results: [{ isFinal: false, length: 1, 0: { transcript: text } }],
  };
}

function finalEvent(text: string) {
  return {
    resultIndex: 0,
    results: [{ isFinal: true, length: 1, 0: { transcript: text } }],
  };
}

const navigationReply: JarvisChatResponse = {
  reply: "Opening your inbox now.",
  action: { type: "navigation", target: "/inbox" },
  used_ai: false,
};

describe("JarvisAssistant · voice barge-in", () => {
  let recog: ReturnType<typeof installFakeRecognition>;
  let speech: ReturnType<typeof installFakeSpeech>;

  async function openPanel() {
    const user = userEvent.setup();
    render(<JarvisAssistant />);
    await user.click(screen.getByTestId("jarvis-launcher"));
    return user;
  }

  async function speakReply(user: ReturnType<typeof userEvent.setup>) {
    await user.type(
      screen.getByLabelText("JARVIS command"),
      "open my inbox{Enter}"
    );
    await waitFor(() => expect(mocks.jarvisChat).toHaveBeenCalledWith("open my inbox"));
    await screen.findByText("Opening your inbox now.");
    const utterance = speech.utterances[0];
    expect(utterance).toBeTruthy();
    return utterance;
  }

  beforeEach(() => {
    vi.clearAllMocks();
    mocks.jarvisChat.mockResolvedValue(navigationReply);
    recog = installFakeRecognition();
    speech = installFakeSpeech();
  });

  afterEach(() => {
    recog.restore();
    speech.restore();
    cleanup();
  });

  it("shows the Speaking state while a reply is read aloud", async () => {
    const user = await openPanel();
    const utterance = await speakReply(user);

    act(() => utterance.onstart?.());
    expect(screen.getByText("Speaking…")).toBeInTheDocument();
    expect(mocks.synthSpeak).toHaveBeenCalledTimes(1);
  });

  it("barge-in cancels TTS and switches to Listening on first speech", async () => {
    const user = await openPanel();
    const utterance = await speakReply(user);
    act(() => utterance.onstart?.());
    expect(screen.getByText("Speaking…")).toBeInTheDocument();

    act(() => {
      recog.instances[0].onresult?.(interimEvent("can you"));
    });

    expect(mocks.synthCancel).toHaveBeenCalled();
    expect(screen.getByText("Listening…")).toBeInTheDocument();
    expect(screen.queryByText("Speaking…")).not.toBeInTheDocument();
    expect(mocks.jarvisChat).toHaveBeenCalledTimes(1);
  });

  it("puts the interrupted speech into the composer without auto-sending", async () => {
    const user = await openPanel();
    const utterance = await speakReply(user);
    act(() => utterance.onstart?.());

    act(() => {
      recog.instances[0].onresult?.(interimEvent("open"));
    });
    act(() => {
      recog.instances[0].onresult?.(
        finalEvent("take me to the dashboard")
      );
    });

    const input = screen.getByLabelText("JARVIS command");
    expect(input).toHaveValue("take me to the dashboard");
    expect(mocks.jarvisChat).toHaveBeenCalledTimes(1);
    expect(mocks.routerPush).toHaveBeenCalledTimes(1); // original inbox nav only
  });

  it("disbands silent capture when speech ends on its own", async () => {
    const user = await openPanel();
    const utterance = await speakReply(user);
    act(() => utterance.onstart?.());
    const instance = recog.instances[0];
    expect(instance.start).toHaveBeenCalledTimes(1); // silent barge-in armed

    act(() => utterance.onend?.());

    expect(instance.stop).toHaveBeenCalled();
    expect(screen.queryByText("Listening…")).not.toBeInTheDocument();
  });

  it("does not disband the capture after a barge-in interruption", async () => {
    const user = await openPanel();
    const utterance = await speakReply(user);
    act(() => utterance.onstart?.());

    act(() => {
      recog.instances[0].onresult?.(interimEvent("stop"));
    });
    const instance = recog.instances[0];
    const stopsBeforeFinal = instance.stop.mock.calls.length;

    act(() => utterance.onend?.());
    expect(instance.stop.mock.calls.length).toBe(stopsBeforeFinal);
    expect(screen.getByText("Listening…")).toBeInTheDocument();
  });

  it("a response that resolves after the panel is closed is discarded", async () => {
    let resolveChat: (value: JarvisChatResponse) => void = () => {};
    mocks.jarvisChat.mockImplementation(
      () =>
        new Promise<JarvisChatResponse>((resolve) => {
          resolveChat = resolve;
        })
    );
    const user = await openPanel();
    await user.type(screen.getByLabelText("JARVIS command"), "hello{Enter}");
    expect(mocks.jarvisChat).toHaveBeenCalledWith("hello");

    await user.click(screen.getByRole("button", { name: "Close JARVIS" }));
    await act(async () => {
      resolveChat({ reply: "late reply", action: null, used_ai: false });
    });

    expect(mocks.routerPush).not.toHaveBeenCalled();
    expect(mocks.synthSpeak).not.toHaveBeenCalled();

    await user.click(screen.getByTestId("jarvis-launcher"));
    expect(screen.queryByText("late reply")).not.toBeInTheDocument();
  });

  it("clicking the mic while speaking cancels TTS and starts listening", async () => {
    const user = await openPanel();
    const utterance = await speakReply(user);
    act(() => utterance.onstart?.());

    await user.click(screen.getByRole("button", { name: "Talk to JARVIS" }));

    expect(mocks.synthCancel).toHaveBeenCalled();
    expect(screen.getByText("Listening…")).toBeInTheDocument();

    act(() => {
      recog.instances[0].onresult?.(
        finalEvent("show me my tasks")
      );
    });
    expect(screen.getByLabelText("JARVIS command")).toHaveValue(
      "show me my tasks"
    );
  });
});