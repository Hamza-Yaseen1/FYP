import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { backendUrl } from "@/lib/api/server";

export async function POST() {
  // Forward the logout request to the backend to clear the session cookie
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("cai_token");

    await fetch(backendUrl("/auth/logout"), {
      method: "POST",
      cache: "no-store",
      headers: {
        Cookie: token ? `cai_token=${token.value}` : "",
      },
    });
  } catch (error) {
    // Continue even if backend call fails - still clear frontend cookie
    console.error("Backend logout failed:", error);
  }

  // Clear the cookie on the frontend response
  const response = NextResponse.json({ ok: true });
  response.cookies.set("cai_token", "", {
    maxAge: 0,
    path: "/",
    httpOnly: true,
    sameSite: "lax",
    secure: false,
  });
  
  return response;
}
