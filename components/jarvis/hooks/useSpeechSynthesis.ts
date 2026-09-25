"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Default soft cap per spoken chunk.
 *
 * Chrome's Web Speech engine truncates a single long utterance: it stops
 * speaking after roughly the first sentence or two and never reaches the rest.
 * Keeping each utterance under this cap (and restarting playback per chunk)
 * keeps long replies reliable. The cap is a *target*, not a hard split —
 * ``chunkForSpeech`` always breaks at sentence boundaries, never mid-word.
 */
const DEFAULT_MAX_CHUNK_CHARS = 280;

function windowHasSpeech(): boolean {
  return (
    typeof window !== "undefined" &&
    "speechSynthesis" in window &&
    typeof window.SpeechSynthesisUtterance !== "undefined"
  );
}

/**
 * Strip speech-unfriendly formatting for spoken output only.
 *
 * The visible reply rendered in the JARVIS panel is never touched — this text
 * is a separate representation used solely for what the voice says.
 */
export function cleanForSpeech(text: string): string {
  let out = String(text ?? "");
  out = out.replace(/```[\s\S]*?```/g, " "); // fenced code blocks
  out = out.replace(/`[^`]*`/g, " "); // inline code
  out = out.replace(/!\[[^\]]*\]\([^)]*\)/g, " "); // images
  out = out.replace(/\[([^\]]*)\]\([^)]*\)/g, "$1"); // links -> spoken label
  out = out.replace(/https?:\/\/\S+/g, "link"); // bare URLs -> "link"
  out = out.replace(/<[^>]+>/g, " "); // stray html tags
  out = out.replace(/^#{1,6}\s+/gm, ""); // markdown headings
  out = out.replace(/^>\s+/gm, ""); // blockquotes
  out = out.replace(/^\s*[-*+]\s+/gm, ""); // bullet markers ("* foo", "- foo")
  out = out.replace(/^\s*\d+[.)]\s+/gm, ""); // numbered list markers ("1. foo")
  out = out.replace(/\*\*([^*]+)\*\*/g, "$1"); // **bold**
  out = out.replace(/(^|[^*])\*([^*]+)\*(?!\*)/g, "$1$2"); // *italic*
  out = out.replace(/__([^_]+)__/g, "$1"); // __bold__
  out = out.replace(/(^|[^_])_([^_]+)_(?!_)/g, "$1$2"); // _italic_
  out = out.replace(/\s+/g, " ").trim();
  return out;
}

/**
 * Split a response into sentence-aligned speech chunks.
 *
 * - Short responses come back as exactly one chunk, so a normal reply keeps
 *   its natural cadence and is never needlessly fragmented.
 * - Longer responses are grouped sentence by sentence up to ``maxChars``.
 *   Splits only ever land on sentence boundaries — never mid-word.
 * - Adjacent short sentences are merged so a long reply never degrades into a
 *   flood of tiny utterances.
 */
export function chunkForSpeech(
  text: string,
  maxChars: number = DEFAULT_MAX_CHUNK_CHARS
): string[] {
  const clean = cleanForSpeech(text);
  if (!clean) return [];
  if (clean.length <= maxChars) return [clean];

  const sentences = clean
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean);
  if (sentences.length <= 1) return [clean]; // one unbreakable sentence

  const chunks: string[] = [];
  let current = "";
  for (const sentence of sentences) {
    const candidate = current ? `${current} ${sentence}` : sentence;
    if (current && candidate.length > maxChars) {
      chunks.push(current);
      current = sentence;
    } else {
      current = candidate;
    }
  }
  if (current) chunks.push(current);
  return chunks;
}

/** Everything ``speakNextChunk`` needs to drive one utterance and recurse. */
interface SpeechDriver {
  session: number;
  sessionRef: React.MutableRefObject<number>;
  queueRef: React.MutableRefObject<string[]>;
  activeRef: React.MutableRefObject<SpeechSynthesisUtterance | null>;
  startRef: React.MutableRefObject<(() => void) | undefined>;
  finish: (session: number) => void;
}

/**
 * Speaks one sentence-group and arms the handlers that advance to the next one
 * (only after the previous ``onend``), release the "speaking" state on a real
 * error, and ignore every event whose session token is stale. Module-scope so
 * the recursive advance has no self-reference-before-declaration problem. All
 * state lives in refs, so the latest handlers are always consulted.
 */
function speakNextChunk(driver: SpeechDriver): void {
  const { session, sessionRef, queueRef, activeRef, startRef, finish } = driver;
  if (session !== sessionRef.current) return;
  if (!windowHasSpeech()) {
    finish(session);
    return;
  }
  const chunk = queueRef.current.shift();
  if (chunk === undefined) {
    finish(session);
    return;
  }

  let startFired = false;
  const utterance = new SpeechSynthesisUtterance(chunk);
  activeRef.current = utterance;
  utterance.onstart = () => {
    if (session !== sessionRef.current) return; // stale — ignore
    if (!startFired) {
      startFired = true;
      startRef.current?.();
    }
  };
  utterance.onend = () => {
    if (session !== sessionRef.current) return; // stale — ignore
    activeRef.current = null;
    if (queueRef.current.length > 0) {
      speakNextChunk(driver); // sequential: next chunk only after this ends
    } else {
      finish(session); // final chunk -> idle
    }
  };
  utterance.onerror = () => {
    // A canceled/interrupted event after our own stop()/speak() belongs to a
    // stale session and is ignored. Anything on the current session aborts the
    // remaining chunks gracefully (finish also clears the queue).
    if (session !== sessionRef.current) return;
    finish(session);
  };
  try {
    window.speechSynthesis.speak(utterance);
  } catch {
    if (session !== sessionRef.current) return;
    finish(session);
  }
}

/**
 * Text-to-speech for JARVIS replies with sequential, sentence-based playback.
 *
 * Design (mirrors the Web Speech reliability fix):
 *
 * - ``speak`` splits the response via ``chunkForSpeech`` and drives ONE
 *   utterance at a time. The next chunk is spoken only after the current
 *   utterance's ``onend`` — never by queueing everything up front. Chrome's
 *   long-utterance truncation bug therefore can't cut the reply short.
 * - A session token guards every callback: ``stop`` / a new ``speak`` bump the
 *   session, so a delayed ``onend``/``onerror`` from an old utterance is
 *   silently ignored and can never flip state or start old chunks while newer
 *   speech is playing.
 * - ``stop`` cancels current audio, clears the remaining queue and invalidates
 *   the session — no queued chunk can start afterwards.
 * - ``onerror`` that is not the result of our own cancel (stale session) aborts
 *   the remaining chunks gracefully and releases the "speaking" state; the
 *   visible text reply is unaffected.
 *
 * ``onStart`` / ``onEnd`` callbacks are kept behind refs so utterances created
 * earlier always invoke the latest handlers.
 */
export function useSpeechSynthesis(options?: {
  onStart?: () => void;
  onEnd?: () => void;
}): {
  speaking: boolean;
  supported: boolean;
  speak: (text: string) => void;
  stop: () => void;
} {
  const [speaking, setSpeaking] = useState(false);
  const [supported] = useState<boolean>(() => windowHasSpeech());

  const startRef = useRef(options?.onStart);
  const endRef = useRef(options?.onEnd);
  useEffect(() => {
    startRef.current = options?.onStart;
    endRef.current = options?.onEnd;
  }, [options]);

  // Session identity: bumped on every speak()/stop(). Any event whose session
  // no longer matches the current one belongs to stale speech and is ignored.
  const sessionRef = useRef(0);
  const queueRef = useRef<string[]>([]);
  const activeRef = useRef<SpeechSynthesisUtterance | null>(null);

  const finish = useCallback((session: number) => {
    if (session !== sessionRef.current) return; // stale — never advance/finish
    queueRef.current = [];
    activeRef.current = null;
    setSpeaking(false);
    endRef.current?.();
  }, []);

  const stop = useCallback(() => {
    sessionRef.current += 1; // invalidate any in-flight session
    queueRef.current = [];
    activeRef.current = null;
    if (windowHasSpeech()) {
      window.speechSynthesis.cancel();
    }
    setSpeaking(false);
  }, []);

  const speak = useCallback(
    (text: string) => {
      if (!windowHasSpeech()) return;
      const chunks = chunkForSpeech(text);
      if (chunks.length === 0) return; // empty / whitespace-only response

      sessionRef.current += 1; // invalidate the previous session first
      window.speechSynthesis.cancel();
      queueRef.current = chunks.slice();
      activeRef.current = null;
      setSpeaking(true);
      speakNextChunk({
        session: sessionRef.current,
        sessionRef,
        queueRef,
        activeRef,
        startRef,
        finish,
      });
    },
    [finish]
  );

  // Prevent speech from continuing after the consuming component unmounts.
  useEffect(() => {
    return () => {
      sessionRef.current += 1;
      queueRef.current = [];
      if (windowHasSpeech()) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  return { speaking, supported, speak, stop };
}