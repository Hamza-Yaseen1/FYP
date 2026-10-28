"use client";

import { useEffect, useState } from "react";
import { apiUrl } from "@/lib/api/config";

export default function HealthBadge() {
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");

  useEffect(() => {
    let cancelled = false;
    fetch(apiUrl("/health"), { credentials: "include", cache: "no-store" })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!cancelled) setStatus(data?.status === "ok" ? "ok" : "error");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const dot =
    status === "ok"
      ? "bg-emerald-500"
      : status === "loading"
        ? "bg-amber-400 animate-pulse"
        : "bg-ember";

  const label =
    status === "ok"
      ? "connected"
      : status === "loading"
        ? "connecting…"
        : "unavailable";

  return (
    <div className="inline-flex items-center gap-1.5 rounded-full border border-border/70 bg-muted/50 px-2.5 py-1 text-xs font-medium text-muted-foreground backdrop-blur-sm">
      <span className={`signal-lamp size-1.5 ${dot}`} aria-hidden />
      backend · {label}
    </div>
  );
}