"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import ConnectionList from "@/components/connections/ConnectionList";
import { Connection, getConnections } from "@/lib/api/connections";

export default function ConnectionsPage() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const searchParams = useSearchParams();
  const gmailStatus = searchParams.get("gmail");

  const fetchConnections = async () => {
    try {
      const data = await getConnections();
      setConnections(data);
    } catch {
      setConnections([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    getConnections()
      .then((data) => {
        if (!cancelled) setConnections(data);
      })
      .catch(() => {
        if (!cancelled) setConnections([]);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Connected Accounts</h1>
      <p className="mt-1 text-sm text-muted-foreground">Channels wired into your desk</p>

      {gmailStatus === "connected" && (
        <div className="mt-4 rounded-xl border border-emerald-300 bg-emerald-50 p-4 text-sm text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950 dark:text-emerald-200">
          Gmail connected successfully. New emails will appear on your dashboard shortly.
        </div>
      )}
      {gmailStatus === "error" && (
        <div className="mt-4 rounded-xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          Gmail connection failed or was denied. You can try connecting again below.
        </div>
      )}

      {isLoading ? (
        <p className="mt-6 text-muted-foreground">Loading connections...</p>
      ) : (
        <div className="mt-6">
          <ConnectionList connections={connections} onRefresh={fetchConnections} />
        </div>
      )}
    </div>
  );
}