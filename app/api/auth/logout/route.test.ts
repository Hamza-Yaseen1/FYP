import { describe, it, expect } from "vitest";
import { POST } from "./route";

describe("POST /api/auth/logout", () => {
  it("returns 200 with { ok: true }", async () => {
    const res = await POST();
    expect(res.status).toBe(200);

    const body = await res.json();
    expect(body).toEqual({ ok: true });
  });

  it("sets cai_token cookie with maxAge=0 to clear it", async () => {
    const res = await POST();
    const setCookie = res.headers.get("set-cookie") ?? "";
    expect(setCookie).toContain("cai_token=");
    expect(setCookie).toMatch(/max-age=0/i);
    expect(setCookie).toContain("Path=/");
  });

  it("marks the cookie as HttpOnly and SameSite=Lax", async () => {
    const res = await POST();
    const setCookie = res.headers.get("set-cookie") ?? "";
    expect(setCookie.toLowerCase()).toContain("httponly");
    expect(setCookie.toLowerCase()).toContain("samesite=lax");
  });

  it("does not include a Secure flag (http dev)", async () => {
    const res = await POST();
    const setCookie = res.headers.get("set-cookie") ?? "";
    expect(setCookie.toLowerCase()).not.toContain("secure");
  });
});
