"use client";

import { useState } from "react";
import { Connection, createConnection, deleteConnection } from "@/lib/api/connections";

interface ConnectionCardProps {
  connection: Connection;
  onConnect?: () => void;
}

const providerIcons: Record<string, string> = {
  whatsapp: "💬",
  gmail: "📧",
  linkedin: "💼",
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
    <div className="flex items-center justify-between p-4 border rounded-lg">
      <div className="flex items-center gap-3">
        <span className="text-2xl">{providerIcons[connection.provider]}</span>
        <div>
          <h3 className="font-medium">{providerNames[connection.provider]}</h3>
          <p className="text-sm text-gray-500">
            {isComingSoon ? "Coming Soon" : connection.status}
          </p>
          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
      </div>
      <div>
        {isComingSoon ? (
          <span className="px-4 py-2 text-sm text-gray-400 bg-gray-100 rounded">
            Coming Soon
          </span>
        ) : isConnected ? (
          <>
            {showConfirm ? (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Disconnect?</span>
                <button
                  onClick={handleDisconnect}
                  disabled={isLoading}
                  className="px-3 py-1 text-sm text-white bg-red-500 rounded hover:bg-red-600 disabled:opacity-50"
                >
                  {isLoading ? "..." : "Yes"}
                </button>
                <button
                  onClick={() => setShowConfirm(false)}
                  disabled={isLoading}
                  className="px-3 py-1 text-sm text-gray-600 bg-gray-200 rounded hover:bg-gray-300 disabled:opacity-50"
                >
                  No
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowConfirm(true)}
                className="px-4 py-2 text-sm text-red-600 bg-red-50 rounded hover:bg-red-100"
              >
                Disconnect
              </button>
            )}
          </>
        ) : (
          <button
            onClick={handleConnect}
            disabled={isLoading}
            className="px-4 py-2 text-sm text-white bg-blue-500 rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {isLoading ? "Connecting..." : "Connect"}
          </button>
        )}
      </div>
    </div>
  );
}
