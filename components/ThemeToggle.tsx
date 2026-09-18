"use client";

import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/lib/theme";
import { useSyncExternalStore } from "react";

function subscribe() {
  return () => {};
}

export default function ThemeToggle({ className }: { className?: string }) {
  const { effectiveTheme, toggleTheme } = useTheme();
  // Check if we're mounted on the client to avoid hydration mismatch
  const mounted = useSyncExternalStore(
    subscribe,
    () => true,
    () => false
  );

  const nextLabel = effectiveTheme === "dark" ? "light" : "dark";

  return (
    <Button
      variant="ghost"
      size="icon"
      className={className}
      onClick={toggleTheme}
      aria-label={`Switch to ${nextLabel} mode`}
      title={`Switch to ${nextLabel} mode`}
    >
      {mounted ? (
        effectiveTheme === "dark" ? <Sun size={18} /> : <Moon size={18} />
      ) : (
        // Render a placeholder with the same dimensions during SSR
        <div style={{ width: 18, height: 18 }} />
      )}
    </Button>
  );
}