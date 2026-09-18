"use client";

import { useEffect, useState } from "react";

export default function HealthBadge() {
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");

  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((res) => res.json())
      .then((data) => setStatus(data.status === "ok" ? "ok" : "error"))
      .catch(() => setStatus("error"));
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
    <div className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-1 text-xs font-medium text-muted-foreground">
      <span className={`signal-lamp size-1.5 ${dot}`} aria-hidden />
      backend · {label}
    </div>
  );
}