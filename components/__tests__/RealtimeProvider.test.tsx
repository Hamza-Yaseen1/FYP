import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import "@testing-library/jest-dom/vitest";
import { act, cleanup, render, screen } from "@testing-library/react";
import { FakeWebSocket } from "./fakeWebSocket";

beforeEach(() => {
  FakeWebSocket.instances = [];
  vi.stubGlobal("WebSocket", FakeWebSocket);
  vi.resetModules();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

async function loadProvider() {
  return import("@/components/RealtimeProvider");
}

describe("RealtimeProvider", () => {
  it("connects and increments version on a realtime event", async () => {
    const { RealtimeProvider, useRealtime } = await loadProvider();

    function Probe() {
      const { connected, version } = useRealtime();
      return <span data-testid="probe">{`${connected}:${version}`}</span>;
    }

    render(
      <RealtimeProvider>
        <Probe />
      </RealtimeProvider>
    );

    const socket = FakeWebSocket.instances[0];
    expect(socket).toBeDefined();
    expect(screen.getByTestId("probe")).toHaveTextContent("false:0");

    act(() => socket.open());
    expect(screen.getByTestId("probe")).toHaveTextContent("true:0");

    act(() => {
      socket.emit({ type: "message.created", message_id: "m1", user_id: "u1" });
    });
    expect(screen.getByTestId("probe")).toHaveTextContent("true:1");
  });

  it("keeps the socket open across unmount (StrictMode-safe)", async () => {
    const { RealtimeProvider } = await loadProvider();

    const { unmount } = render(
      <RealtimeProvider>
        <span />
      </RealtimeProvider>
    );
    const socket = FakeWebSocket.instances[0];
    expect(socket).toBeDefined();
    act(() => socket.open());

    unmount();

    // Unmount must not close a live socket; React StrictMode would otherwise
    // tear the connection down mid-handshake in development.
    expect(socket.readyState).toBe(FakeWebSocket.OPEN);
  });

  it("keeps polling while the socket is disconnected", async () => {
    vi.useFakeTimers();
    const { RealtimeProvider, useRealtime } = await loadProvider();

    function Probe() {
      const { version } = useRealtime();
      return <span data-testid="version">{version}</span>;
    }

    render(
      <RealtimeProvider>
        <Probe />
      </RealtimeProvider>
    );
    expect(screen.getByTestId("version").textContent).toBe("0");

    // Socket never opens, so the fallback tick should fire.
    act(() => {
      vi.advanceTimersByTime(15_000);
    });
    expect(screen.getByTestId("version").textContent).toBe("1");
  });
});
