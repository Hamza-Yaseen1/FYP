"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Connection, createConnection, deleteConnection } from "@/lib/api/connections";

interface ConnectionCardProps {
  connection: Connection;
  onConnect?: () => void;
}

const providerDots: Record<string, string> = {
  whatsapp: "bg-emerald-500",
  gmail: "bg-cool",
  linkedin: "bg-dim",
};

const providerNames: Record<string, string> = {
  whatsapp: "WhatsApp",
  gmail: "Gmail",
  linkedin: "LinkedIn",
};

export default function ConnectionCard({ connection, onConnect }: ConnectionCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);

  const isComingSoon = connection.status === "coming_soon";
  const isConnected = connection.status === "connected";

  const handleConnect = async () => {
    if (connection.provider === "linkedin") return;

    setIsLoading(true);
    setError(null);

    try {
      await createConnection(connection.provider as "whatsapp" | "gmail");
      onConnect?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to connect");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnect = async () => {
    setIsLoading(true);
    setError(null);

    try {
      await deleteConnection(connection.id);
      setShowConfirm(false);
      onConnect?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to disconnect");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3.5">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-xl border border-border bg-muted">
          <span
            className={`signal-lamp size-2 ${providerDots[connection.provider] ?? "bg-dim"}`}
            aria-hidden
          />
        </span>
        <div>
          <h3 className="text-sm font-semibold">{providerNames[connection.provider]}</h3>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {isComingSoon ? (
              "Coming soon"
            ) : isConnected ? (
              <span className="inline-flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
                <span className="signal-lamp size-1.5 bg-emerald-500" aria-hidden />
                Connected
              </span>
            ) : (
              "Not connected"
            )}
          </p>
          {error && <p className="mt-1 text-sm text-ember">{error}</p>}
        </div>
      </div>
      <div>
        {isComingSoon ? (
          <span className="inline-flex rounded-full border border-border bg-muted px-3 py-1.5 text-xs font-medium text-muted-foreground">
            Soon
          </span>
        ) : isConnected ? (
          <>
            {showConfirm ? (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Disconnect?</span>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleDisconnect}
                  disabled={isLoading}
                >
                  {isLoading ? "…" : "Yes"}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowConfirm(false)}
                  disabled={isLoading}
                >
                  No
                </Button>
              </div>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowConfirm(true)}
                className="text-destructive hover:text-destructive"
              >
                Disconnect
              </Button>
            )}
          </>
        ) : (
          <Button onClick={handleConnect} disabled={isLoading}>
            {isLoading ? "Connecting…" : "Connect"}
          </Button>
        )}
      </div>
    </div>
  );
}