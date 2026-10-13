/**
 * Browser WebSocket client for real-time dashboard updates.
 *
 * A single connection per tab is shared through a module-level singleton.
 * It auto-reconnects with exponential backoff and exposes a `connected` flag
 * so the UI can fall back to polling while the socket is down.
 *
 * Authentication mirrors the REST API: the httpOnly session cookie is sent on
 * the handshake. In local development the browser may drop that cookie on a
 * cross-port handshake, so an opt-in short-lived token is fetched from the
 * authenticated `GET /ws-token` endpoint and passed as `?token=`. That fallback
 * is enabled with `NEXT_PUBLIC_WS_USE_TOKEN=true` (defaulting to on in `next
 * dev`, off in production) and only works when the backend sets
 * `WS_ALLOW_QUERY_TOKEN=true`.
 *
 * Events are produced by the backend (`message.created` / `message.updated`)
 * and only ever concern the logged-in user.
 */

export type RealtimeEventType = "message.created" | "message.updated";

export interface RealtimeEvent {
  type: RealtimeEventType;
  message_id: string;
  user_id: string;
}

type EventListener = (event: RealtimeEvent) => void;
type StatusListener = (connected: boolean) => void;

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

const BASE_BACKOFF_MS = 1000;
const MAX_BACKOFF_MS = 15000;

/**
 * Whether the dev-only `?token=` handshake fallback should be used.
 *
 * `NEXT_PUBLIC_WS_USE_TOKEN` wins when set; otherwise the fallback is on for
 * `next dev` and off for production builds, so production auth stays
 * cookie-only.
 */
export function wsTokenEnabled(): boolean {
  const flag = process.env.NEXT_PUBLIC_WS_USE_TOKEN;
  if (flag === "true") return true;
  if (flag === "false") return false;
  return process.env.NODE_ENV === "development";
}

/** Fetch a short-lived WebSocket token for the current session (dev fallback). */
export async function fetchWsToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  try {
    const res = await fetch(`${API_BASE}/ws-token`, {
      credentials: "include",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) return null;
    const data = (await res.json()) as { token?: unknown };
    return typeof data?.token === "string" ? data.token : null;
  } catch {
    return null;
  }
}

/**
 * Resolve the backend WebSocket URL.
 *
 * Priority:
 * 1. `NEXT_PUBLIC_WS_URL` (explicit — recommended in production).
 * 2. `NEXT_PUBLIC_API_BASE` when it is an absolute URL (http→ws, https→wss).
 * 3. Same hostname as the app, backend port 8000 (local development).
 *
 * The socket connects to FastAPI directly rather than through the Next.js
 * rewrite: Next.js handlers/rewrites are not a reliable WebSocket proxy.
 */
function resolveWebSocketBase(): string {
  const explicit = process.env.NEXT_PUBLIC_WS_URL;
  if (explicit) return explicit;
  if (typeof window === "undefined") return "";

  const apiBase = process.env.NEXT_PUBLIC_API_BASE;
  if (apiBase && /^https?:\/\//i.test(apiBase)) {
    return `${apiBase.replace(/^https?/i, (m) => (m.toLowerCase() === "https" ? "wss" : "ws"))}/ws`;
  }
  return `ws://${window.location.hostname}:8000/ws`;
}

/**
 * Build the WebSocket URL, optionally appending a short-lived dev token.
 * When `token` is omitted the handshake relies on the session cookie alone.
 */
export function buildWebSocketUrl(token?: string): string {
  const base = resolveWebSocketBase();
  if (!base || !token) return base;
  const separator = base.includes("?") ? "&" : "?";
  return `${base}${separator}token=${encodeURIComponent(token)}`;
}

export type WsTokenProvider = () => Promise<string | null>;

export class RealtimeClient {
  private ws: WebSocket | null = null;
  private eventListeners = new Set<EventListener>();
  private statusListeners = new Set<StatusListener>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private tokenProvider: WsTokenProvider | null = null;
  private attempts = 0;
  private connecting = false;
  private manuallyClosed = false;
  private connected = false;

  isConnected(): boolean {
    return this.connected;
  }

  /** Install (or clear) the dev-only token source used on each connect. */
  setTokenProvider(provider: WsTokenProvider | null): void {
    this.tokenProvider = provider;
  }

  async connect(): Promise<void> {
    if (typeof window === "undefined") return;
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.OPEN ||
        this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }
    if (this.connecting) return;

    this.manuallyClosed = false;
    this.connecting = true;

    let token: string | null = null;
    if (this.tokenProvider) {
      try {
        token = await this.tokenProvider();
      } catch {
        token = null;
      }
    }
    this.connecting = false;

    // A disconnect (or another connect) landed while the token was in flight.
    if (this.manuallyClosed) return;
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.OPEN ||
        this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    const url = buildWebSocketUrl(token ?? undefined);
    if (!url) return;

    let socket: WebSocket;
    try {
      socket = new WebSocket(url);
    } catch {
      this.scheduleReconnect();
      return;
    }
    this.ws = socket;

    socket.onopen = () => {
      if (this.ws !== socket) return;
      this.attempts = 0;
      this.setConnected(true);
    };

    socket.onmessage = (event: MessageEvent) => {
      if (this.ws !== socket) return;
      let parsed: RealtimeEvent | null = null;
      try {
        parsed = JSON.parse(String(event.data)) as RealtimeEvent;
      } catch {
        parsed = null;
      }
      if (!parsed || typeof parsed.type !== "string") return;
      this.eventListeners.forEach((listener) => listener(parsed as RealtimeEvent));
    };

    socket.onclose = () => {
      // Ignore a stale socket's close so it cannot clobber a newer one.
      if (this.ws !== socket) return;
      this.ws = null;
      this.setConnected(false);
      if (!this.manuallyClosed) this.scheduleReconnect();
    };

    socket.onerror = () => {
      // `onclose` always follows an error; reconnect is handled there.
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer || this.manuallyClosed) return;
    const delay = Math.min(BASE_BACKOFF_MS * 2 ** this.attempts, MAX_BACKOFF_MS);
    this.attempts += 1;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      void this.connect();
    }, delay);
  }

  private setConnected(next: boolean): void {
    if (this.connected === next) return;
    this.connected = next;
    this.statusListeners.forEach((listener) => listener(next));
  }

  disconnect(): void {
    this.manuallyClosed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      try {
        this.ws.close();
      } catch {
        // Ignore — the socket was already closing.
      }
      this.ws = null;
    }
    this.setConnected(false);
  }

  subscribe(listener: EventListener): () => void {
    this.eventListeners.add(listener);
    return () => {
      this.eventListeners.delete(listener);
    };
  }

  subscribeStatus(listener: StatusListener): () => void {
    this.statusListeners.add(listener);
    return () => {
      this.statusListeners.delete(listener);
    };
  }
}

let singleton: RealtimeClient | null = null;

export function getRealtimeClient(): RealtimeClient {
  if (!singleton) singleton = new RealtimeClient();
  return singleton;
}
