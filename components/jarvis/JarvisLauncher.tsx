"use client";

import { Sparkles } from "lucide-react";
import JarvisOrb from "./JarvisOrb";

export default function JarvisLauncher({
  state,
  onClick,
}: {
  state: "idle" | "listening" | "thinking" | "speaking";
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-label="Open JARVIS"
      data-testid="jarvis-launcher"
      onClick={onClick}
      className="group fixed right-4 bottom-4 z-40 flex items-center gap-2 rounded-full border border-border/60 glass-card p-2 pr-3.5 pastel-shadow transition-transform hover:scale-[1.03] active:scale-[0.98]"
    >
      <JarvisOrb state={state} size="sm" />
      <span className="flex items-center gap-1.5 text-sm font-medium text-foreground">
        <Sparkles
          size={14}
          className="text-signal transition-transform group-hover:rotate-12"
        />
        JARVIS
      </span>
    </button>
  );
}