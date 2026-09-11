"use client";

import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/lib/theme";

export default function ThemeToggle({ className }: { className?: string }) {
  const { effectiveTheme, toggleTheme } = useTheme();
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
      {effectiveTheme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
    </Button>
  );
}