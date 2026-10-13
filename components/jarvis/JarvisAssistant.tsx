"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { jarvisChat } from "@/lib/api/jarvis";
import JarvisLauncher from "./JarvisLauncher";
import JarvisPanel from "./JarvisPanel";
import { useSpeechRecognition } from "./hooks/useSpeechRecognition";
import { useSpeechSynthesis } from "./hooks/useSpeechSynthesis";
import type { JarvisAction, JarvisMessage, JarvisOrbState } from "./types";

export default function JarvisAssistant() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<JarvisMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [pendingConfirmation, setPendingConfirmation] =
    useState<JarvisAction | null>(null);
  const [composerText, setComposerText] = useState("");
  const router = useRouter();

  const {
    speak,
    stop: stopSpeech,
    speaking,
    supported: ttsSupported,
  } = useSpeechSynthesis({
    onStart: handleSpeechStart,
    onEnd: handleSpeechEnd,
  });

  const {
    listening,
    supported: micSupported,
    toggle: toggleMic,
    stop: stopListening,
    startSilent,
    showListening,
  } = useSpeechRecognition(handleFinalTranscript, handleSpeechActivity);

  const pushReply = (text: string, action?: JarvisAction | null) => {
    setMessages((prev) => [...prev, { role: "assistant", text, action }]);
  };

  const applyNavigation = (response: { action: JarvisAction | null }) => {
    if (response.action?.type === "navigation" && response.action.target) {
      router.push(response.action.target);
    }
  };

  // ── Voice barge-in orchestration ──────────────────────────────────────────
  // Refs mirror live values so the recognition/synthesis hooks' latest-callback
  // semantics never run on stale state (busy, confirmation lock, speech mood).

  const generationRef = useRef(0);
  const silentRef = useRef(false); // recognition armed while JARVIS speaks
  const captureRef = useRef(false); // currently capturing an interrupted phrase
  const listeningRef = useRef(false);
  const speakingRef = useRef(false);
  const lockedRef = useRef(false);

  useEffect(() => {
    listeningRef.current = listening;
  }, [listening]);
  useEffect(() => {
    speakingRef.current = speaking;
  }, [speaking]);
  useEffect(() => {
    lockedRef.current = Boolean(pendingConfirmation);
  }, [pendingConfirmation]);

  const stopSpeechRef = useRef(stopSpeech);
  const startSilentRef = useRef(startSilent);
  const showListeningRef = useRef(showListening);
  const stopListeningRef = useRef(stopListening);
  const toggleMicRef = useRef(toggleMic);
  useEffect(() => {
    stopSpeechRef.current = stopSpeech;
    startSilentRef.current = startSilent;
    showListeningRef.current = showListening;
    stopListeningRef.current = stopListening;
    toggleMicRef.current = toggleMic;
  });

  function handleSpeechStart() {
    // A reply is being spoken: arm silent barge-in capture (no "Listening" UI
    // until the user actually starts talking). Never overrides manual capture.
    if (micSupported && !listeningRef.current && !lockedRef.current) {
      silentRef.current = true;
      startSilentRef.current();
    }
  }

  function handleSpeechEnd() {
    // Speech finished without being interrupted — disband the silent capture.
    if (!captureRef.current && silentRef.current) {
      silentRef.current = false;
      stopListeningRef.current();
    }
  }

  function handleSpeechActivity(text: string) {
    if (!text.trim()) return;
    // Only react when a spoken reply was actually playing (barge-in). Interim
    // chunks during a manual mic session are handled by the final transcript.
    if (!silentRef.current && !speakingRef.current) return;

    captureRef.current = true;
    silentRef.current = false;
    generationRef.current += 1; // any in-flight reply is now stale
    setBusy(false);
    stopSpeechRef.current();
    showListeningRef.current();
  }

  function handleFinalTranscript(text: string) {
    const trimmed = text.trim();
    if (!trimmed || lockedRef.current) return;
    captureRef.current = false;
    silentRef.current = false;
    setComposerText(trimmed);
  }

  const sendCommand = async (raw: string) => {
    const text = raw.trim();
    if (!text || busy || pendingConfirmation) return;
    const generation = ++generationRef.current;
    setBusy(true);
    setMessages((prev) => [...prev, { role: "user", text }]);
    try {
      const response = await jarvisChat(text);
      if (generation !== generationRef.current) return;
      pushReply(response.reply, response.action);
      if (response.action?.type === "request_confirmation") {
        setPendingConfirmation(response.action);
      } else {
        applyNavigation(response);
      }
      if (ttsSupported) {
        speak(response.reply);
      }
    } catch {
      if (generation === generationRef.current) {
        pushReply("Sorry, I could not reach the server. Please try again.");
      }
    } finally {
      if (generation === generationRef.current) setBusy(false);
    }
  };

  const settleConfirmation = async (
    message: JarvisMessage,
    confirmed: boolean
  ) => {
    const token = message.action?.confirmation_token;
    if (!token || confirming || pendingConfirmation !== message.action) return;
    const generation = ++generationRef.current;
    setConfirming(true);
    try {
      const response = await jarvisChat("", {
        confirmation_token: token,
        confirmed,
      });
      if (generation !== generationRef.current) return;
      pushReply(response.reply, response.action);
      applyNavigation(response);
      if (ttsSupported) {
        speak(response.reply);
      }
    } catch {
      if (generation === generationRef.current) {
        pushReply("Sorry, I could not reach the server. Please try again.");
      }
    } finally {
      if (generation === generationRef.current) {
        setConfirming(false);
        setPendingConfirmation(null);
      }
    }
  };

  const handleToggleMic = () => {
    if (busy || lockedRef.current) return;
    if (speakingRef.current) {
      // Explicitly interrupting the spoken reply behaves like a barge-in:
      // cancel TTS first, then start a visible capture.
      captureRef.current = true;
      silentRef.current = false;
      generationRef.current += 1;
      setBusy(false);
      stopSpeechRef.current();
    }
    toggleMicRef.current();
  };

  const locked = Boolean(pendingConfirmation);

  const orState: JarvisOrbState = listening
    ? "listening"
    : busy || confirming
      ? "thinking"
      : speaking
        ? "speaking"
        : "idle";

  return (
    <>
      {!open && <JarvisLauncher state={orState} onClick={() => setOpen(true)} />}
      <JarvisPanel
        open={open}
        state={orState}
        messages={messages}
        micSupported={micSupported}
        listening={listening}
        busy={busy}
        confirming={confirming}
        pendingConfirmation={locked}
        onConfirm={(message) => void settleConfirmation(message, true)}
        onCancel={(message) => void settleConfirmation(message, false)}
        onSend={(text) => void sendCommand(text)}
        composerValue={composerText}
        onComposerChange={setComposerText}
        onToggleMic={handleToggleMic}
        onClose={() => {
          generationRef.current += 1;
          setOpen(false);
          stopListening();
          stopSpeech();
        }}
      />
    </>
  );
}