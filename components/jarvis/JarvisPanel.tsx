"use client";

import { useEffect, useRef, useState } from "react";
import { Mic, Send, X } from "lucide-react";
import { ASSISTANT_NAME } from "@/lib/brand";
import JarvisOrb from "./JarvisOrb";
import JarvisStatus from "./JarvisStatus";
import type { JarvisAction, JarvisMessage, JarvisOrbState } from "./types";

interface JarvisPanelProps {
  open: boolean;
  state: JarvisOrbState;
  messages: JarvisMessage[];
  micSupported: boolean;
  listening: boolean;
  busy: boolean;
  onSend: (text: string) => void;
  onToggleMic: () => void;
  onClose: () => void;
  confirming?: boolean;
  pendingConfirmation?: boolean;
  onConfirm?: (message: JarvisMessage) => void;
  onCancel?: (message: JarvisMessage) => void;
  /** Controlled composer value (used by JarvisAssistant to fill from speech). */
  composerValue?: string;
  onComposerChange?: (value: string) => void;
}

function confirmationSummary(action: JarvisAction): string | null {
  const summary = action.detail?.summary;
  return typeof summary === "string" && summary.trim() ? summary : null;
}

function draftText(action: JarvisAction): string | null {
  const draft = action.detail?.draft;
  return typeof draft === "string" && draft.trim() ? draft : null;
}

export default function JarvisPanel({
  open,
  state,
  messages,
  micSupported,
  listening,
  busy,
  onSend,
  onToggleMic,
  onClose,
  confirming = false,
  pendingConfirmation = false,
  onConfirm = () => {},
  onCancel = () => {},
  composerValue,
  onComposerChange,
}: JarvisPanelProps) {
  // Uncontrolled fallback when no `composerValue` is supplied (existing
  // consumers); rendering with the assistant is fully controlled.
  const [internalDraft, setInternalDraft] = useState("");
  const draft = composerValue ?? internalDraft;
  const setDraftValue = (value: string) => {
    if (onComposerChange) {
      onComposerChange(value);
    } else {
      setInternalDraft(value);
    }
  };
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, open]);

  if (!open) return null;

  const locked = busy || confirming || pendingConfirmation;

  const submit = () => {
    const text = draft.trim();
    if (!text || locked) return;
    setDraftValue("");
    onSend(text);
  };

  return (
    <div
      className="jarvis-panel-enter fixed right-4 bottom-20 z-50 flex w-[min(26rem,calc(100vw-2rem))] flex-col overflow-hidden rounded-2xl glass-card border border-border pastel-shadow"
      data-testid="jarvis-panel"
      data-open="true"
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-3 border-b border-border/60 px-4 py-3">
        <div className="flex items-center gap-3">
          <JarvisOrb state={state} size="sm" />
          <JarvisStatus state={state} />
        </div>
        <button
          type="button"
          aria-label={`Close ${ASSISTANT_NAME}`}
          onClick={onClose}
          className="grid size-7 place-items-center rounded-lg text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        >
          <X size={16} />
        </button>
      </div>

      {/* Transcript */}
      <div
        ref={scrollRef}
        className="flex max-h-72 min-h-40 flex-col gap-2 overflow-y-auto px-4 py-3"
      >
        {messages.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Try “Show my inbox”, “How many unread messages do I have?”, or
            “What needs my attention?”.
          </p>
        ) : (
          messages.map((message, index) =>
            message.role === "user" ? (
              <div
                key={index}
                className="self-end max-w-[85%] rounded-2xl rounded-br-sm bg-signal px-3 py-2 text-sm text-primary-foreground"
              >
                {message.text}
              </div>
            ) : (
              <div
                key={index}
                className="self-start max-w-[85%] rounded-2xl rounded-bl-sm bg-surface-2 px-3 py-2 text-sm text-foreground"
              >
                {message.text}
                {message.action?.type === "request_confirmation" && (
                  <>
                    {confirmationSummary(message.action) && (
                      <div
                        className="mt-2 whitespace-pre-line rounded-lg border border-dashed border-border bg-surface-1 px-3 py-2 text-xs text-muted-foreground"
                        data-testid="jarvis-pending-summary"
                      >
                        {confirmationSummary(message.action)}
                      </div>
                    )}
                    <div className="mt-2 flex items-center gap-2">
                      <button
                        type="button"
                        aria-label={`Confirm ${ASSISTANT_NAME} action`}
                        onClick={() => onConfirm(message)}
                        disabled={confirming || busy}
                        data-action="confirm"
                        className={
                          confirming
                            ? "cursor-not-allowed rounded-lg bg-signal px-3 py-1.5 text-xs font-medium text-primary-foreground opacity-60"
                            : "rounded-lg bg-signal px-3 py-1.5 text-xs font-medium text-primary-foreground transition-opacity hover:bg-signal-strong disabled:opacity-40"
                        }
                      >
                        {confirming ? "Working…" : "Confirm"}
                      </button>
                      <button
                        type="button"
                        aria-label={`Cancel ${ASSISTANT_NAME} action`}
                        onClick={() => onCancel(message)}
                        disabled={confirming || busy}
                        data-action="cancel"
                        className="rounded-lg px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:opacity-40"
                      >
                        Cancel
                      </button>
                    </div>
                  </>
                )}
                {message.action?.type === "draft_reply" &&
                  draftText(message.action) && (
                    <div
                      className="mt-2 rounded-lg border border-dashed border-ember/40 bg-surface-1 px-3 py-2"
                      data-testid="jarvis-draft-block"
                    >
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-ember">
                        Draft · not sent
                      </p>
                      <p className="mt-1 whitespace-pre-line text-xs text-muted-foreground">
                        {draftText(message.action)}
                      </p>
                    </div>
                  )}
              </div>
            )
          )
        )}
      </div>

      {/* Composer */}
      <div className="flex items-center gap-2 border-t border-border/60 px-3 py-3">
        <button
          type="button"
          aria-label={listening ? "Stop listening" : `Talk to ${ASSISTANT_NAME}`}
          onClick={onToggleMic}
          disabled={!micSupported || pendingConfirmation}
          className={
            !micSupported || pendingConfirmation
              ? "grid size-8 shrink-0 cursor-not-allowed place-items-center rounded-lg text-muted-foreground/40"
              : listening
                ? "grid size-8 shrink-0 place-items-center rounded-lg bg-ember/15 text-ember transition-colors hover:bg-ember/25"
                : "grid size-8 shrink-0 place-items-center rounded-lg text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          }
        >
          <Mic size={16} />
        </button>
        <input
          type="text"
          value={draft}
          onChange={(event) => setDraftValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") submit();
          }}
          disabled={pendingConfirmation}
          placeholder={
            pendingConfirmation
              ? "Confirm or cancel your pending action…"
              : micSupported
                ? "Type a command or tap the mic…"
                : "Type a command…"
          }
          aria-label={`${ASSISTANT_NAME} command`}
          className="h-8 min-w-0 flex-1 rounded-lg bg-surface-2 px-3 text-sm text-foreground outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-ring/40 disabled:cursor-not-allowed disabled:opacity-50"
        />
        <button
          type="button"
          aria-label="Send command"
          onClick={submit}
          disabled={busy || confirming || pendingConfirmation || draft.trim() === ""}
          className="grid size-8 shrink-0 place-items-center rounded-lg bg-signal text-primary-foreground transition-opacity hover:bg-signal-strong disabled:opacity-40"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}