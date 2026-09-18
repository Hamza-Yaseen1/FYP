const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// ── Response cache (GET-only, TTL + in-flight dedup) ─────────────────────

interface CacheEntry {
  data: unknown;
  expiresAt: number;
}

const DEFAULT_TTL_MS = 10_000;

/** url → CacheEntry */
const cache = new Map<string, CacheEntry>();

/** url → Promise for an in-flight request (dedupes identical concurrent GETs) */
const inflight = new Map<string, Promise<unknown>>();

function cacheKey(path: string, options?: RequestInit): string | null {
  const method = (options?.method ?? "GET").toUpperCase();
  if (method !== "GET") return null;
  // opt-out via cache: "no-store"
  if (options?.cache === "no-store") return null;
  return `${method}:${API_BASE}${path}`;
}

function cachedGet<T>(key: string, path: string, options?: RequestInit): Promise<T> {
  // return cached value if still fresh
  const entry = cache.get(key);
  if (entry && entry.expiresAt > Date.now()) {
    return Promise.resolve(entry.data as T);
  }

  // dedupe identical in-flight request
  const existing = inflight.get(key);
  if (existing) return existing as Promise<T>;

  const ttl = DEFAULT_TTL_MS;

  const promise = fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  })
    .then(async (res) => {
      if (res.status === 401 && typeof window !== "undefined") {
        // eslint-disable-next-line @next/next/no-location-assign-relative-destination
        window.location.assign("/login");
        throw new ApiError(401, "Not authenticated");
      }
      let data: unknown = null;
      const text = await res.text();
      if (text) {
        try { data = JSON.parse(text); } catch { data = null; }
      }
      if (!res.ok) {
        const detail =
          data && typeof data === "object" && "detail" in data
            ? String((data as { detail: unknown }).detail)
            : `Request failed with status ${res.status}`;
        throw new ApiError(res.status, detail);
      }
      cache.set(key, { data, expiresAt: Date.now() + ttl });
      return data as T;
    })
    .finally(() => {
      inflight.delete(key);
    });

  inflight.set(key, promise);
  return promise;
}

/**
 * Invalidate cached entries. If `path` is given only that entry is removed;
 * otherwise the full cache is cleared (use after mutations).
 */
export function clearCache(path?: string): void {
  if (!path) {
    cache.clear();
    return;
  }
  for (const k of cache.keys()) {
    if (k.endsWith(path)) cache.delete(k);
  }
}

// ── Main fetch wrapper ───────────────────────────────────────────────────

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const { headers, ...rest } = options;

  const key = cacheKey(path, options);
  if (key) return cachedGet<T>(key, path, options);

  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(headers ?? {}),
    },
    ...rest,
  });

  if (res.status === 401 && typeof window !== "undefined") {
    // Full page navigation is intentional: it clears all cached client
    // state after session loss. This module sits outside React context,
    // so useRouter is unavailable here.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.assign("/login");
    throw new ApiError(401, "Not authenticated");
  }

  let data: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!res.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : `Request failed with status ${res.status}`;
    throw new ApiError(res.status, detail);
  }

  return data as T;
}
