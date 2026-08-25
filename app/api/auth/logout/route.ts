import { NextResponse } from "next/server";
import { cookies } from "next/headers";

export async function POST() {
  // Forward the logout request to the backend to clear the session cookie
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("cai_token");
    
    await fetch("http://localhost:8000/auth/logout", {
      method: "POST",
      credentials: "include",
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
