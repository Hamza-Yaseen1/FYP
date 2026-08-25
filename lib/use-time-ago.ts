"use client";

import { useEffect, useState } from "react";
import { timeAgo } from "@/lib/time-ago";

export function useTimeAgo(dateString: string): string {
  const [label, setLabel] = useState(() => timeAgo(dateString));
  const [prevDateString, setPrevDateString] = useState(dateString);

  if (prevDateString !== dateString) {
    setPrevDateString(dateString);
    setLabel(timeAgo(dateString));
  }

  useEffect(() => {
    const interval = setInterval(() => setLabel(timeAgo(dateString)), 30_000);
    return () => clearInterval(interval);
  }, [dateString]);

  return label;
}
