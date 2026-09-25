import { describe, it, expect, vi, afterEach } from "vitest";
import { jarvisChat } from "@/lib/api/jarvis";

afterEach(() => {
  vi.unstubAllGlobals();
});

const ok = (body: unknown) =>
  new Response(JSON.stringify(body), { status: 200 });

describe("jarvisChat", () => {
  it("POSTs the message to /jarvis/chat with credentials", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      ok({
        reply: "Opening your inbox.",
        action: { type: "navigation", target: "/inbox" },
        used_ai: false,
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await jarvisChat("take me to inbox");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/jarvis/chat");
    expect(init.method).toBe("POST");
    expect(init.credentials).toBe("include");
    expect(JSON.parse(init.body)).toEqual({ message: "take me to inbox" });
    expect(result).toEqual({
      reply: "Opening your inbox.",
      action: { type: "navigation", target: "/inbox" },
      used_ai: false,
    });
  });

  it("round-trips the confirmation token and decided flag", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      ok({
        reply: "Done. I've created the task.",
        action: { type: "create_task", detail: { title: "finish docs" } },
        used_ai: false,
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await jarvisChat("", {
      confirmation_token: "tok-123",
      confirmed: true,
    });

    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      message: "",
      confirmation_token: "tok-123",
      confirmed: true,
    });
    expect(result.action?.type).toBe("create_task");
  });

  it("sends confirmed:false to cancel a pending action", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      ok({
        reply: "Understood — I have not made any changes.",
        action: null,
        used_ai: false,
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    await jarvisChat("", { confirmation_token: "tok-123", confirmed: false });

    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      message: "",
      confirmation_token: "tok-123",
      confirmed: false,
    });
  });

  it("propagates backend errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Message cannot be empty." }), {
          status: 400,
        })
      )
    );
    await expect(jarvisChat("")).rejects.toThrow("Message cannot be empty.");
  });
});