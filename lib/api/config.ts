/**
 * Browser-facing API configuration.
 *
 * `NEXT_PUBLIC_API_BASE` is the single source of truth for every request made
 * from the browser. Keep it as the relative `/api` prefix so requests stay
 * same-origin and are proxied to the backend by the Next.js rewrite in
 * `next.config.ts` (this is what keeps the httpOnly session cookie working).
 *
 * Set it to an absolute backend URL only when the backend is configured for
 * cross-origin credentialed requests (CORS + SameSite=None cookies).
 */
const DEFAULT_API_BASE = "/api";

function normalizeBase(value: string | undefined, fallback: string): string {
  const trimmed = value?.trim();
  if (!trimmed) return fallback;
  return trimmed.replace(/\/+$/, "") || fallback;
}

export const API_BASE = normalizeBase(
  process.env.NEXT_PUBLIC_API_BASE,
  DEFAULT_API_BASE
);

/** Build a URL for an API path, tolerant of a leading slash on either side. */
export function apiUrl(path: string): string {
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${suffix}`;
}
