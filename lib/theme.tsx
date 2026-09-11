"use client";

import * as React from "react";

export type Theme = "light" | "dark" | "system";

const STORAGE_KEY = "theme";

function getStoredTheme(): Theme {
  if (typeof window === "undefined") return "system";
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    return value === "light" || value === "dark" || value === "system"
      ? value
      : "system";
  } catch {
    return "system";
  }
}

const DARK_MODE_QUERY = "(prefers-color-scheme: dark)";

function subscribeMedia(onStoreChange: () => void): () => void {
  const mq = window.matchMedia(DARK_MODE_QUERY);
  mq.addEventListener("change", onStoreChange);
  return () => mq.removeEventListener("change", onStoreChange);
}

function getMediaSnapshot(): boolean {
  return window.matchMedia(DARK_MODE_QUERY).matches;
}

function getMediaServerSnapshot(): boolean {
  return false;
}

function toEffective(theme: Theme, prefersDark: boolean): "light" | "dark" {
  if (theme === "system") return prefersDark ? "dark" : "light";
  return theme;
}

interface ThemeContextValue {
  theme: Theme;
  effectiveTheme: "light" | "dark";
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = React.createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = React.useState<Theme>(getStoredTheme);
  const prefersDark = React.useSyncExternalStore(
    subscribeMedia,
    getMediaSnapshot,
    getMediaServerSnapshot
  );

  const setTheme = React.useCallback((next: Theme) => {
    setThemeState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Private mode or storage unavailable — keep in-memory only.
    }
  }, []);

  const effectiveTheme = toEffective(theme, prefersDark);

  const toggleTheme = React.useCallback(() => {
    const next = effectiveTheme === "dark" ? "light" : "dark";
    setTheme(next);
  }, [effectiveTheme, setTheme]);

  React.useEffect(() => {
    document.documentElement.classList.toggle("dark", effectiveTheme === "dark");
  }, [effectiveTheme]);

  return (
    <ThemeContext.Provider
      value={{ theme, effectiveTheme, setTheme, toggleTheme }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const ctx = React.useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within a ThemeProvider");
  return ctx;
}