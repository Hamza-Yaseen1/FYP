import type { NextConfig } from "next";

const DEV_BACKEND_URL = "http://localhost:8000";
const rawBackendUrl = process.env.BACKEND_URL?.trim();

if (rawBackendUrl && !/^https?:\/\//i.test(rawBackendUrl)) {
  throw new Error(
    `BACKEND_URL must be an absolute http(s) URL (received "${rawBackendUrl}"). ` +
      "Example: BACKEND_URL=https://fyp-omega-peach.vercel.app"
  );
}

if (!rawBackendUrl) {
  const message =
    "BACKEND_URL is not set. Set it in .env.local (local development) or in " +
    "your hosting provider's environment variables before deploying.";
  if (process.env.NODE_ENV === "production") {
    throw new Error(message);
  }
  console.warn(`[next.config] ${message} Falling back to ${DEV_BACKEND_URL}.`);
}

// Normalize so `https://host/` and `https://host` produce the same rewrite
// destination (a trailing slash would otherwise create `https://host//path`).
const BACKEND_URL = (rawBackendUrl || DEV_BACKEND_URL).replace(/\/+$/, "");

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;
