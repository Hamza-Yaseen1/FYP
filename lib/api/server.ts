/**
 * Server-only backend configuration used by Next.js Route Handlers.
 *
 * `BACKEND_URL` is not a `NEXT_PUBLIC_` variable on purpose: it is only read
 * on the server so the internal backend address is never shipped to browsers.
 */
function normalizeBackendUrl(value: string | undefined): string {
  const trimmed = value?.trim();
  if (!trimmed) {
    throw new Error(
      "BACKEND_URL is not configured. Add " +
        "BACKEND_URL=https://your-backend.example.com to .env.local (and to " +
        "your hosting provider's environment variables), then restart the " +
        "server."
    );
  }

  if (!/^https?:\/\//i.test(trimmed)) {
    throw new Error(
      `BACKEND_URL must be an absolute http(s) URL (received "${trimmed}").`
    );
  }

  return trimmed.replace(/\/+$/, "");
}

/** Build an absolute backend URL for a server-side request. */
export function backendUrl(path = ""): string {
  const base = normalizeBackendUrl(process.env.BACKEND_URL);
  if (!path) return base;
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}
