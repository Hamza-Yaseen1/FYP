"use client";

import { useTheme, type Theme } from "@/lib/theme";
import { cn } from "@/lib/utils";

const options: { value: Theme; label: string; description: string }[] = [
  { value: "light", label: "Light", description: "Purple on white" },
  { value: "dark", label: "Dark", description: "Purple on gray-black" },
  { value: "system", label: "System", description: "Follow your device" },
];

export default function AppearanceSettings() {
  const { theme, setTheme } = useTheme();

  return (
    <div>
      <div className="grid gap-2 sm:grid-cols-3">
        {options.map((option) => {
          const active = theme === option.value;
          return (
            <button
              key={option.value}
              onClick={() => setTheme(option.value)}
              aria-pressed={active}
              className={cn(
                "flex flex-col items-start gap-1 rounded-xl border p-4 text-left transition-colors",
                active
                  ? "border-primary/40 bg-primary/5 ring-1 ring-primary/30"
                  : "border-border bg-card hover:border-muted-foreground/40"
              )}
            >
              <span
                className={cn(
                  "flex w-full items-center justify-between text-sm font-medium",
                  active && "text-primary"
                )}
              >
                {option.label}
                <span
                  className={cn(
                    "size-4 rounded-full border",
                    active
                      ? "border-primary bg-primary"
                      : "border-muted-foreground/40"
                  )}
                  aria-hidden
                />
              </span>
              <span className="text-xs text-muted-foreground">
                {option.description}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}