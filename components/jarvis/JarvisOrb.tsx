"use client";

import { ASSISTANT_NAME } from "@/lib/brand";
import { cn } from "@/lib/utils";
import type { JarvisOrbState } from "./types";

const stateClass: Record<JarvisOrbState, string> = {
  idle: "jarvis-orb--idle",
  listening: "jarvis-orb--listening",
  thinking: "jarvis-orb--thinking",
  speaking: "jarvis-orb--speaking",
};

/**
 * The JARVIS status orb. Pure presentational: the `state` class switches the
 * CSS animations (glow, expanding rings, spinning scan arc) defined in
 * app/globals.css.
 */
export default function JarvisOrb({
  state,
  size = "md",
  className,
}: {
  state: JarvisOrbState;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const sizeClass =
    size === "sm" ? "size-8" : size === "lg" ? "size-14" : "size-10";

  return (
    <div
      role="status"
      aria-label={`${ASSISTANT_NAME} ${state}`}
      aria-live="polite"
      data-state={state}
      className={cn(
        "jarvis-orb relative shrink-0 rounded-full",
        sizeClass,
        stateClass[state],
        className
      )}
    >
      <span className="jarvis-orb__core relative block h-full w-full rounded-full" />
    </div>
  );
}