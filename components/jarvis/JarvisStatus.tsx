"use client";

import type { JarvisOrbState } from "./types";

const labels: Record<JarvisOrbState, string> = {
  idle: "JARVIS ready",
  listening: "Listening…",
  thinking: "Thinking…",
  speaking: "Speaking…",
};

export default function JarvisStatus({
  state,
  className,
}: {
  state: JarvisOrbState;
  className?: string;
}) {
  return (
    <span
      data-status={state}
      className={`triage-label text-muted-foreground ${className ?? ""}`}
    >
      {labels[state]}
    </span>
  );
}