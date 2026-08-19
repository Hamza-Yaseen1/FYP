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

  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <span
        className={`size-2 rounded-full ${
          status === "ok"
            ? "bg-emerald-500"
            : status === "loading"
              ? "bg-yellow-500 animate-pulse"
              : "bg-red-500"
        }`}
      />
      Backend:{" "}
      {status === "ok"
        ? "Connected"
        : status === "loading"
          ? "Connecting..."
          : "Unavailable"}
    </div>
  );
}
