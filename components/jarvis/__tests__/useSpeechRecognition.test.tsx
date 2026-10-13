import { describe, it, expect, vi, afterEach } from "vitest";
import { act, cleanup, renderHook } from "@testing-library/react";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";

/**
 * Simulates the real browser `SpeechRecognitionEvent`: transcripts are only
 * reachable via `event.results` (result list). `event` itself has no `length`
 * and is not indexable — the regression this file guards against is reading
 * transcripts from the event object instead of `event.results`.
 */
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

function buildEvent(resultIndex: number, results: unknown[]) {
  return { resultIndex, results };
}

describe("useSpeechRecognition", () => {
  let fake: ReturnType<typeof installFakeRecognition>;

  afterEach(() => {
    fake?.restore();
    cleanup();
  });

  it("exposes supported=false when the browser has no SpeechRecognition", () => {
    const { result } = renderHook(() => useSpeechRecognition(vi.fn()));
    expect(result.current.supported).toBe(false);
    expect(result.current.listening).toBe(false);
  });

  it("extracts the final transcript from event.results and auto-stops", () => {
    fake = installFakeRecognition();
    const onFinal = vi.fn();
    const { result } = renderHook(() => useSpeechRecognition(onFinal));

    expect(result.current.supported).toBe(true);
    act(() => result.current.toggle());
    expect(result.current.listening).toBe(true);

    const instance = fake.instances[0];
    expect(instance.start).toHaveBeenCalledTimes(1);
    expect(instance.onresult).toBeTruthy();

    act(() => {
      instance.onresult?.(buildEvent(0, [{ isFinal: true, length: 1, 0: { transcript: "Hello Jarvis" } }]));
    });

    expect(onFinal).toHaveBeenCalledWith("Hello Jarvis");
    expect(instance.stop).toHaveBeenCalledTimes(1);
  });

  it("fires ONLY for final results, ignoring interim chunks", () => {
    fake = installFakeRecognition();
    const onFinal = vi.fn();
    const { result } = renderHook(() => useSpeechRecognition(onFinal));
    act(() => result.current.toggle());
    const instance = fake.instances[0];

    act(() => {
      instance.onresult?.(buildEvent(0, [{ isFinal: false, length: 1, 0: { transcript: "Hello" } }]));
    });
    expect(onFinal).not.toHaveBeenCalled();
    expect(instance.stop).not.toHaveBeenCalled();

    act(() => {
      instance.onresult?.(buildEvent(0, [{ isFinal: true, length: 1, 0: { transcript: "Hello Jarvis" } }]));
    });
    expect(onFinal).toHaveBeenCalledWith("Hello Jarvis");
  });

  it("does not re-read finalized results before event.resultIndex", () => {
    fake = installFakeRecognition();
    const onFinal = vi.fn();
    const { result } = renderHook(() => useSpeechRecognition(onFinal));
    act(() => result.current.toggle());
    const instance = fake.instances[0];

    act(() => {
      instance.onresult?.(buildEvent(6, [{ isFinal: true, length: 1, 0: { transcript: "skipped" } }]));
    });
    expect(onFinal).not.toHaveBeenCalled();
  });

  it("switches listening off when recognition ends", () => {
    fake = installFakeRecognition();
    const { result } = renderHook(() => useSpeechRecognition(vi.fn()));
    act(() => result.current.toggle());
    expect(result.current.listening).toBe(true);

    act(() => fake.instances[0].onend?.());
    expect(result.current.listening).toBe(false);
  });

  it("reports interim chunks via onSpeechActivity without stopping", () => {
    fake = installFakeRecognition();
    const onActivity = vi.fn();
    const onFinal = vi.fn();
    const { result } = renderHook(() =>
      useSpeechRecognition(onFinal, onActivity)
    );
    act(() => result.current.toggle());
    const instance = fake.instances[0];
    expect(instance.interimResults).toBe(true);

    act(() => {
      instance.onresult?.(
        buildEvent(0, [{ isFinal: false, length: 1, 0: { transcript: "Hello" } }])
      );
    });

    expect(onActivity).toHaveBeenCalledWith("Hello");
    expect(onFinal).not.toHaveBeenCalled();
    expect(instance.stop).not.toHaveBeenCalled();
  });

  it("startSilent arms capture without showing the listening UI", () => {
    fake = installFakeRecognition();
    const { result } = renderHook(() => useSpeechRecognition(vi.fn()));
    expect(result.current.listening).toBe(false);

    act(() => result.current.startSilent());
    expect(fake.instances[0].start).toHaveBeenCalledTimes(1);
    expect(result.current.listening).toBe(false);

    act(() => result.current.showListening());
    expect(result.current.listening).toBe(true);
  });

  it("toggle while silently running promotes instead of double-starting", () => {
    fake = installFakeRecognition();
    const { result } = renderHook(() => useSpeechRecognition(vi.fn()));
    act(() => result.current.startSilent());
    expect(result.current.listening).toBe(false);

    act(() => result.current.toggle());
    expect(result.current.listening).toBe(true);
    expect(fake.instances[0].start).toHaveBeenCalledTimes(1);
  });

  it("silent capture is disbanded when recognition ends", () => {
    fake = installFakeRecognition();
    const { result } = renderHook(() => useSpeechRecognition(vi.fn()));
    act(() => result.current.startSilent());
    expect(result.current.listening).toBe(false);

    act(() => fake.instances[0].onend?.());
    expect(result.current.listening).toBe(false);

    act(() => result.current.startSilent());
    expect(fake.instances[0].start).toHaveBeenCalledTimes(2);
  });
});