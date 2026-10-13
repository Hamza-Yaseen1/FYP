"use client";

import { createContext, useContext, useEffect, useState } from "react";
import {
  fetchWsToken,
  getRealtimeClient,
  wsTokenEnabled,
  type RealtimeEvent,
} from "@/lib/realtime";

interface RealtimeContextValue {
  connected: boolean;
  version: number;
  lastEvent: RealtimeEvent | null;
}

const RealtimeContext = createContext<RealtimeContextValue>({
  connected: false,
  version: 0,
  lastEvent: null,
});

const FALLBACK_POLL_MS = 15000;

/**
 * Owns the realtime connection for the dashboard.
 *
 * The connection lives at app scope (a module singleton), not at component
 * scope: React StrictMode's mount→unmount→mount in development would otherwise
 * close a socket that is still CONNECTING, surfacing the browser warning
 * "WebSocket is closed before the connection is established." Unmount only
 * detaches listeners; the socket is closed explicitly on logout.
 *
 * While the socket is down the provider ticks `version` on an interval so the
 * UI keeps updating via the pre-WebSocket polling paths.
 */
export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const [connected, setConnected] = useState(false);
  const [version, setVersion] = useState(0);
  const [lastEvent, setLastEvent] = useState<RealtimeEvent | null>(null);

  useEffect(() => {
    const client = getRealtimeClient();
    const unsubscribeStatus = client.subscribeStatus(setConnected);
    const unsubscribeEvents = client.subscribe((event) => {
      setLastEvent(event);
      setVersion((v) => v + 1);
    });

    if (wsTokenEnabled()) {
      client.setTokenProvider(fetchWsToken);
    }
    void client.connect();

    return () => {
      unsubscribeEvents();
      unsubscribeStatus();
    };
  }, []);

  useEffect(() => {
    if (connected) return;
    const id = setInterval(() => setVersion((v) => v + 1), FALLBACK_POLL_MS);
    return () => clearInterval(id);
  }, [connected]);

  return (
    <RealtimeContext.Provider value={{ connected, version, lastEvent }}>
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtime(): RealtimeContextValue {
  return useContext(RealtimeContext);
}
