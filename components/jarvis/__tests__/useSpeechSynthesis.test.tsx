import { describe, it, expect, vi, afterEach } from "vitest";
import { act, cleanup, renderHook } from "@testing-library/react";
import {
  chunkForSpeech,
  cleanForSpeech,
  useSpeechSynthesis,
} from "../hooks/useSpeechSynthesis";

interface FakeUtteranceCtor {
  new (text: string): FakeUtterance;
}

interface FakeUtterance {
  text: string;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
}

/** Installs a fake window.speechSynthesis + SpeechSynthesisUtterance and
 * records every spoken utterance for the test to drive manually. */
function installFakeSpeech() {
  const spoken: FakeUtterance[] = [];
  let active: FakeUtterance | null = null;

  const synth = {
    speak: vi.fn((utterance: FakeUtterance) => {
      active = utterance;
    }),
    cancel: vi.fn(() => {
      active?.onerror?.({ error: "canceled" });
      active = null;
    }),
    paused: false,
    pending: false,
    speaking: false,
  };

  const speechDescriptor = Object.getOwnPropertyDescriptor(
    window,
    "speechSynthesis"
  );
  const utteranceDescriptor = Object.getOwnPropertyDescriptor(
    window,
    "SpeechSynthesisUtterance"
  );

  function endActive() {
    active = null;
  }

  Object.defineProperty(window, "speechSynthesis", {
    value: synth,
    configurable: true,
    writable: true,
  });
  class FakeSpeechSynthesisUtterance implements FakeUtterance {
    text: string;
    onstart: (() => void) | null = null;
    onend: (() => void) | null = null;
    onerror: ((event: { error?: string }) => void) | null = null;
    constructor(text: string) {
      this.text = text;
      spoken.push(this);
    }
  }
  Object.defineProperty(window, "SpeechSynthesisUtterance", {
    value: FakeSpeechSynthesisUtterance,
    configurable: true,
    writable: true,
  });

  return {
    spoken,
    synth,
    utteranceCtor: FakeSpeechSynthesisUtterance as unknown as FakeUtteranceCtor,
    /** Marks the current utterance as ended (as the engine would). */
    endActive,
    active: () => active,
    restore() {
      if (speechDescriptor) {
        Object.defineProperty(window, "speechSynthesis", speechDescriptor);
      } else {
        delete (
          window as Partial<Window> & { speechSynthesis?: unknown }
        ).speechSynthesis;
      }
      if (utteranceDescriptor) {
        Object.defineProperty(
          window,
          "SpeechSynthesisUtterance",
          utteranceDescriptor
        );
      } else {
        delete (
          window as Partial<Window> & { SpeechSynthesisUtterance?: unknown }
        ).SpeechSynthesisUtterance;
      }
    },
  };
}

function makeSentence(i: number): string {
  return `Message number ${i} describes important details about your project status and what happened today.`;
}

function longReply(): string {
  return [1, 2, 3, 4, 5].map(makeSentence).join(" ");
}

describe("cleanForSpeech", () => {
  it("strips markdown bullets, bold, headers and links", () => {
    const text = "# Summary\n\n**Today** you received:\n- one urgent\n- two normal\nsee [the docs](https://example.com)\n\n*Done.*";
    expect(cleanForSpeech(text)).toBe(
      "Summary Today you received: one urgent two normal see the docs Done."
    );
  });

  it("replaces bare urls and collapses whitespace", () => {
    expect(cleanForSpeech("Check https://a.b.c/x now.")).toBe(
      "Check link now."
    );
  });

  it("treats empty and whitespace-only text as empty", () => {
    expect(cleanForSpeech("")).toBe("");
    expect(cleanForSpeech("   \n  ")).toBe("");
  });
});

describe("chunkForSpeech", () => {
  it("keeps short replies as a single chunk", () => {
    expect(chunkForSpeech("You have 3 unread messages.")).toEqual([
      "You have 3 unread messages.",
    ]);
  });

  it("splits long replies on sentence boundaries without smashing words", () => {
    const chunks = chunkForSpeech(longReply());
    expect(chunks.length).toBeGreaterThan(1);
    for (const chunk of chunks) {
      expect(chunk.length).toBeLessThanOrEqual(350);
      const lastChar = chunk[chunk.length - 1];
      expect([".", "!", "?"]).toContain(lastChar);
    }
    expect(chunks.join(" ")).toBe(
      cleanForSpeech(longReply())
    );
  });

  it("merges adjacent short sentences instead of emitting tiny chunks", () => {
    const chunks = chunkForSpeech("Aaa. Bbb. Ccc. Ddd.", 10);
    expect(chunks.length).toBe(2);
    expect(chunks[0]).toBe("Aaa. Bbb.");
    expect(chunks[1]).toBe("Ccc. Ddd.");
  });

  it("does not split a single unbreakable long sentence", () => {
    const long = "no punctuation ".repeat(30).trim();
    const chunks = chunkForSpeech(long, 100);
    expect(chunks).toEqual([long]);
  });

  it("returns an empty array for empty input", () => {
    expect(chunkForSpeech("   ")).toEqual([]);
  });
});

describe("useSpeechSynthesis", () => {
  let fake: ReturnType<typeof installFakeSpeech>;

  afterEach(() => {
    fake?.restore();
    cleanup();
  });

  it("reports supported=false and no-ops when the browser has no speech", () => {
    const { result } = renderHook(() => useSpeechSynthesis());
    expect(result.current.supported).toBe(false);
    expect(() => {
      act(() => result.current.speak("Hello there."));
      act(() => result.current.stop());
    }).not.toThrow();
    expect(result.current.speaking).toBe(false);
  });

  it("speaks a short reply as a single cleaned utterance", () => {
    fake = installFakeSpeech();
    const onStart = vi.fn();
    const onEnd = vi.fn();
    const { result } = renderHook(() =>
      useSpeechSynthesis({ onStart, onEnd })
    );

    act(() => result.current.speak("**You** have 3 unread messages."));
    expect(result.current.speaking).toBe(true);
    expect(fake.spoken.length).toBe(1);
    expect(fake.spoken[0].text).toBe("You have 3 unread messages.");

    act(() => fake.spoken[0].onstart?.());
    expect(onStart).toHaveBeenCalledTimes(1);

    act(() => fake.spoken[0].onend?.());
    expect(result.current.speaking).toBe(false);
    expect(onEnd).toHaveBeenCalledTimes(1);
  });

  it("plays long replies one chunk at a time, advancing only after onend", () => {
    fake = installFakeSpeech();
    const onStart = vi.fn();
    const onEnd = vi.fn();
    const { result } = renderHook(() =>
      useSpeechSynthesis({ onStart, onEnd })
    );

    act(() => result.current.speak(longReply()));
    expect(result.current.speaking).toBe(true);
    expect(fake.spoken.length).toBe(1); // only the first chunk is queued up front

    act(() => fake.spoken[0].onstart?.());
    expect(onStart).toHaveBeenCalledTimes(1);
    act(() => fake.spoken[0].onend?.());
    expect(fake.spoken.length).toBe(2); // chunk 2 created only after chunk 1 ends
    act(() => fake.spoken[1].onend?.());
    expect(fake.spoken.length).toBe(3);
    expect(result.current.speaking).toBe(true); // still mid-playback

    act(() => fake.spoken[fake.spoken.length - 1].onend?.());
    expect(result.current.speaking).toBe(false); // final chunk -> idle
    expect(onEnd).toHaveBeenCalledTimes(1);
  });

  it("stop() cancels current audio and drops all queued chunks", () => {
    fake = installFakeSpeech();
    const { result } = renderHook(() => useSpeechSynthesis());

    act(() => result.current.speak(longReply()));
    expect(fake.spoken.length).toBe(1);

    act(() => result.current.stop());
    expect(result.current.speaking).toBe(false);
    expect(fake.synth.cancel).toHaveBeenCalled();

    // Late engine events from the cancelled run are stale and must be ignored.
    expect(() => {
      act(() => fake.spoken[0].onend?.());
      act(() => fake.spoken[0].onerror?.({ error: "canceled" }));
    }).not.toThrow();
    expect(result.current.speaking).toBe(false);
    expect(fake.spoken.length).toBe(1); // no queued chunk was ever spoken
  });

  it("a stale interrupted response cannot resume after a newer speak()", () => {
    fake = installFakeSpeech();
    const { result } = renderHook(() => useSpeechSynthesis());

    act(() => result.current.speak(longReply()));
    act(() => fake.spoken[0].onend?.());
    const responseAChunk2 = fake.spoken[1];
    expect(responseAChunk2).toBeTruthy();

    act(() => result.current.speak("Quick interruption."));
    const responseB = fake.spoken[fake.spoken.length - 1];
    expect(result.current.speaking).toBe(true);

    // Response A's chunk 2 now ends / errors late — it must be ignored.
    act(() => responseAChunk2.onend?.());
    act(() => responseAChunk2.onerror?.({ error: "canceled" }));
    expect(result.current.speaking).toBe(true); // B unaffected
    expect(fake.spoken[fake.spoken.length - 1]).toBe(responseB);

    act(() => responseB.onend?.());
    expect(result.current.speaking).toBe(false);
  });

  it("a real synthesis error aborts the remaining chunks gracefully", () => {
    fake = installFakeSpeech();
    const onEnd = vi.fn();
    const { result } = renderHook(() => useSpeechSynthesis({ onEnd }));

    act(() => result.current.speak(longReply()));
    act(() => fake.spoken[0].onerror?.({ error: "synthesis-failed" }));
    expect(result.current.speaking).toBe(false);
    expect(onEnd).toHaveBeenCalledTimes(1);
    expect(fake.spoken.length).toBe(1); // rest never spoken
  });

  it("a browser-driven cancel (current session) aborts cleanly", () => {
    fake = installFakeSpeech();
    const onEnd = vi.fn();
    const { result } = renderHook(() => useSpeechSynthesis({ onEnd }));

    act(() => result.current.speak(longReply()));
    act(() => fake.spoken[0].onerror?.({ error: "canceled" }));
    expect(result.current.speaking).toBe(false);
    expect(onEnd).toHaveBeenCalledTimes(1);
  });

  it("empty and whitespace-only replies never touch the speech engine", () => {
    fake = installFakeSpeech();
    const { result } = renderHook(() => useSpeechSynthesis());

    act(() => result.current.speak("   \n  "));
    expect(result.current.speaking).toBe(false);
    expect(fake.spoken.length).toBe(0);
    expect(fake.synth.speak).not.toHaveBeenCalled();
  });

  it("cancels speech when the consuming component unmounts", () => {
    fake = installFakeSpeech();
    const { result, unmount } = renderHook(() => useSpeechSynthesis());

    act(() => result.current.speak(longReply()));
    expect(fake.spoken.length).toBe(1);
    act(() => unmount());
    expect(fake.synth.cancel).toHaveBeenCalled();

    // Stale events after unmount must not crash or change state.
    expect(() => {
      act(() => fake.spoken[0].onend?.());
    }).not.toThrow();
  });
});