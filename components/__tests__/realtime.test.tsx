import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { RealtimeClient, buildWebSocketUrl } from "@/lib/realtime";
import { FakeWebSocket } from "./fakeWebSocket";

beforeEach(() => {
  FakeWebSocket.instances = [];
  vi.stubGlobal("WebSocket", FakeWebSocket);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("buildWebSocketUrl", () => {
  const originalWsUrl = process.env.NEXT_PUBLIC_WS_URL;
  const originalApiBase = process.env.NEXT_PUBLIC_API_BASE;

  afterEach(() => {
    if (originalWsUrl === undefined) delete process.env.NEXT_PUBLIC_WS_URL;
    else process.env.NEXT_PUBLIC_WS_URL = originalWsUrl;
    if (originalApiBase === undefined) delete process.env.NEXT_PUBLIC_API_BASE;
    else process.env.NEXT_PUBLIC_API_BASE = originalApiBase;
  });

  it("prefers an explicit NEXT_PUBLIC_WS_URL", () => {
    process.env.NEXT_PUBLIC_WS_URL = "wss://api.example.com/ws";
    expect(buildWebSocketUrl()).toBe("wss://api.example.com/ws");
  });

  it("derives ws:// from an absolute NEXT_PUBLIC_API_BASE", () => {
    delete process.env.NEXT_PUBLIC_WS_URL;
    process.env.NEXT_PUBLIC_API_BASE = "https://api.example.com";
    expect(buildWebSocketUrl()).toBe("wss://api.example.com/ws");
  });

  it("falls back to the backend port on the current host", () => {
    delete process.env.NEXT_PUBLIC_WS_URL;
    delete process.env.NEXT_PUBLIC_API_BASE;
    expect(buildWebSocketUrl()).toBe("ws://localhost:8000/ws");
  });
});

describe("RealtimeClient", () => {
  it("reports connected on open and dispatches events", () => {
    const client = new RealtimeClient();
    const events: unknown[] = [];
    const statuses: boolean[] = [];
    client.subscribe((event) => events.push(event));
    client.subscribeStatus((status) => statuses.push(status));

    client.connect();
    const socket = FakeWebSocket.instances[0];
    expect(socket).toBeDefined();
    expect(client.isConnected()).toBe(false);

    socket.open();
    expect(client.isConnected()).toBe(true);
    expect(statuses).toContain(true);

    socket.emit({ type: "message.created", message_id: "m1", user_id: "u1" });
    expect(events).toEqual([
      { type: "message.created", message_id: "m1", user_id: "u1" },
    ]);
  });

  it("ignores malformed payloads", () => {
    const client = new RealtimeClient();
    const listener = vi.fn();
    client.subscribe(listener);
    client.connect();
    const socket = FakeWebSocket.instances[0];
    socket.open();

    socket.emitRaw("not json");
    socket.emitRaw(JSON.stringify({ noType: true }));

    expect(listener).not.toHaveBeenCalled();
  });

  it("reconnects with backoff after an unexpected close", () => {
    vi.useFakeTimers();
    const client = new RealtimeClient();
    client.connect();
    expect(FakeWebSocket.instances).toHaveLength(1);

    FakeWebSocket.instances[0].close();
    expect(FakeWebSocket.instances).toHaveLength(1);

    vi.advanceTimersByTime(1000);
    expect(FakeWebSocket.instances).toHaveLength(2);
  });

  it("does not reconnect after an explicit disconnect", () => {
    vi.useFakeTimers();
    const client = new RealtimeClient();
    client.connect();
    client.disconnect();

    vi.advanceTimersByTime(1000);
    expect(FakeWebSocket.instances).toHaveLength(1);
  });

  it("appends a dev token to the handshake URL", () => {
    const url = buildWebSocketUrl("tok.abc");
    expect(url).toBe("ws://localhost:8000/ws?token=tok.abc");
  });

  it("uses the token provider on connect", async () => {
    const client = new RealtimeClient();
    client.setTokenProvider(async () => "tok-123");

    await client.connect();

    const socket = FakeWebSocket.instances[0];
    expect(socket).toBeDefined();
    expect(socket.url).toBe("ws://localhost:8000/ws?token=tok-123");
  });

  it("still connects (cookie-only) when the token provider yields null", async () => {
    const client = new RealtimeClient();
    client.setTokenProvider(async () => null);

    await client.connect();

    const socket = FakeWebSocket.instances[0];
    expect(socket).toBeDefined();
    expect(socket.url).toBe("ws://localhost:8000/ws");
  });

  it("does not open a second socket while one is active", () => {
    const client = new RealtimeClient();
    client.connect();
    client.connect();
    expect(FakeWebSocket.instances).toHaveLength(1);
  });
});
