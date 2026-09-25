"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/** One `SpeechRecognitionResult` — a chunk (`isFinal`) of recognized speech. */
interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  [index: number]: { transcript: string };
}

/** Web Speech `SpeechRecognitionResultList` — i.e. `event.results`. */
interface SpeechRecognitionResultList {
  length: number;
  [index: number]: SpeechRecognitionResult;
}

/**
 * `SpeechRecognitionEvent`. The transcripts live under `event.results` —
 * the event object itself is NOT array-like and has no `length`, so it must
 * never be indexed directly (`event[0]` is always undefined).
 */
interface SpeechRecognitionEventShape {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionInstance {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: SpeechRecognitionEventShape) => void) | null;
  onend: (() => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
  start: () => void;
  stop: () => void;
}

type RecognitionConstructor = new () => SpeechRecognitionInstance;

export function getSpeechRecognition(): RecognitionConstructor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    webkitSpeechRecognition?: RecognitionConstructor;
    SpeechRecognition?: RecognitionConstructor;
  };
  return w.webkitSpeechRecognition ?? w.SpeechRecognition ?? null;
}

/**
 * Browser speech-to-text.
 *
 * `onFinalTranscript` fires with each finalized utterance (the transcript
 * lives under ``event.results``). `onSpeechActivity` fires on interim chunks
 * so a caller can react the moment the user starts talking (voice barge-in).
 *
 * Two start modes, so the UI can arm the microphone invisibly while JARVIS is
 * speaking and only show "Listening" once real speech is detected:
 *
 * - ``toggle``: the visible mic button (starts with the listening UI).
 * - ``startSilent``: arms recognition without flipping the listening UI;
 *   ``showListening`` promotes it once speech is detected. If the mic is
 *   already running (visible or silent) ``toggle`` either stops or promotes
 *   it instead of double-starting the instance.
 */
export function useSpeechRecognition(
  onFinalTranscript: (text: string) => void,
  onSpeechActivity?: (text: string) => void
): {
  listening: boolean;
  supported: boolean;
  toggle: () => void;
  stop: () => void;
  startSilent: () => void;
  showListening: () => void;
} {
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const startedRef = useRef(false);
  const [listening, setListening] = useState(false);
  const [supported] = useState<boolean>(() => getSpeechRecognition() !== null);

  // Always call the latest handlers even though the recognition instance is
  // created once (avoids stale closures over busy/confirming state).
  const callbackRef = useRef(onFinalTranscript);
  const activityRef = useRef(onSpeechActivity);
  useEffect(() => {
    callbackRef.current = onFinalTranscript;
    activityRef.current = onSpeechActivity;
  }, [onFinalTranscript, onSpeechActivity]);

  const ensureRecognition = useCallback((): SpeechRecognitionInstance | null => {
    const Constructor = getSpeechRecognition();
    if (!Constructor) return null;
    if (!recognitionRef.current) {
      const recognition = new Constructor();
      recognition.lang = "en-US";
      recognition.interimResults = true;
      recognition.continuous = false;
      recognition.onresult = (event) => {
        // Transcripts come from `event.results` (a result list), never from
        // the event itself — `event` has no `length` and is not indexable.
        let finalText = "";
        let interimText = "";
        const results = event.results;
        for (let i = event.resultIndex ?? 0; i < (results?.length ?? 0); i++) {
          const item = results[i];
          if (!item) continue;
          const chunk = item[0] ? item[0].transcript : "";
          if (item.isFinal) {
            finalText += chunk;
          } else if (!interimText) {
            interimText = chunk;
          }
        }
        if (interimText.trim()) {
          activityRef.current?.(interimText.trim());
        }
        if (finalText.trim()) {
          try {
            recognition.stop();
          } catch {
            // already done
          }
          callbackRef.current(finalText.trim());
        }
      };
      recognition.onend = () => {
        startedRef.current = false;
        setListening(false);
      };
      recognition.onerror = () => {
        startedRef.current = false;
        setListening(false);
      };
      recognitionRef.current = recognition;
    }
    return recognitionRef.current;
  }, []);

  const stop = useCallback(() => {
    startedRef.current = false;
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // not active
      }
    }
    setListening(false);
  }, []);

  const startSilent = useCallback(() => {
    const recognition = ensureRecognition();
    if (!recognition || startedRef.current) return;
    try {
      recognition.start();
      startedRef.current = true;
    } catch {
      startedRef.current = false;
    }
  }, [ensureRecognition]);

  const showListening = useCallback(() => setListening(true), []);

  const toggle = useCallback(() => {
    const recognition = ensureRecognition();
    if (!recognition) return;
    if (listening) {
      stop();
      return;
    }
    if (startedRef.current) {
      // Already running (silent barge-in) — promote to a visible capture.
      showListening();
      return;
    }
    try {
      recognition.start();
      startedRef.current = true;
      setListening(true);
    } catch {
      startedRef.current = false;
      setListening(false);
    }
  }, [ensureRecognition, listening, showListening, stop]);

  return { listening, supported, toggle, stop, startSilent, showListening };
}