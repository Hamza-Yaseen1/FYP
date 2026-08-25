"use client";

import { Connection } from "@/lib/api/connections";
import ConnectionCard from "./ConnectionCard";

interface ConnectionListProps {
  connections: Connection[];
  onRefresh?: () => void;
}

const allProviders = [
  { provider: "whatsapp" as const, status: "disconnected" as const },
  { provider: "gmail" as const, status: "disconnected" as const },
  { provider: "linkedin" as const, status: "coming_soon" as const },
];

export default function ConnectionList({ connections, onRefresh }: ConnectionListProps) {
  const displayProviders = allProviders.map((p) => {
    const existing = connections.find((c) => c.provider === p.provider);
    return existing || { ...p, id: "", created_at: "" };
  });

  return (
    <div className="space-y-4">
      {displayProviders.map((provider) => (
        <ConnectionCard
          key={provider.provider}
          connection={provider}
          onConnect={onRefresh}
        />
      ))}
    </div>
  );
}
