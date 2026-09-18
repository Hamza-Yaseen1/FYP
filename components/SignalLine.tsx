"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface Counts {
  tabs?: {
    all: number;
    urgent: number;
    important: number;
    normal: number;
    unread: number;
  };
}

interface SignalState {
  total: number;
  urgent: number;
  important: number;
  ready: boolean;
}

export default function SignalLine() {
  const [state, setState] = useState<SignalState>({
    total: 0,
    urgent: 0,
    important: 0,
    ready: false,
  });

  useEffect(() => {
    let cancelled = false;
    apiFetch<Counts>("/messages/counts")
      .then((data) => {
        if (cancelled) return;
        const t = data?.tabs;
        setState({
          total: t?.all ?? 0,
          urgent: t?.urgent ?? 0,
          important: t?.important ?? 0,
          ready: true,
        });
      })
      .catch(() => {
        if (!cancelled) setState((s) => ({ ...s, ready: true }));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const needYouNow = state.urgent + state.important;

  return (
    <div className="flex h-9 shrink-0 items-center gap-3 overflow-x-auto border-b border-border px-4 sm:px-6">
      {!state.ready ? (
        <span className="text-xs text-muted-foreground">Reading…</span>
      ) : (
        <>
          <div className="flex flex-1 items-center gap-x-3 gap-y-0.5 whitespace-nowrap text-xs text-muted-foreground">
            <span>
              {state.total} message{state.total !== 1 ? "s" : ""} in
            </span>
            <span className="text-muted-foreground/40">·</span>
            <span>{state.important} important</span>
            <span className="hidden text-muted-foreground/40 sm:inline">·</span>
            <span className="hidden sm:inline">{state.urgent} need you now</span>
          </div>

          <span
            className={`ml-auto flex shrink-0 items-center gap-1.5 text-xs font-medium ${
              needYouNow > 0 ? "text-primary" : "text-muted-foreground"
            }`}
          >
            <span
              className={`signal-lamp size-1.5 ${
                needYouNow > 0 ? "bg-primary" : "bg-dim"
              }`}
              aria-hidden
            />
            {needYouNow > 0 ? "Action needed" : "All quiet"}
          </span>
        </>
      )}
    </div>
  );
}