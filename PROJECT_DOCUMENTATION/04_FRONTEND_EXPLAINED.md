# 04 — Frontend Explained

> How the Sift web app is built, screen by screen, and how data flows from the browser to the backend and back. Beginner-friendly first, then the technical detail.

---

## 1. The big picture

The frontend is a **Next.js 16 App Router** application written in **TypeScript** and styled with **Tailwind CSS v4**. It has three kinds of pages:

1. **Public pages** (`/`, `/privacy`, `/terms`) — visible to anyone.
2. **Auth pages** (`/login`, `/signup`, `/forgot-password`, `/reset-password`) — for signed-out users.
3. **Dashboard pages** (`/dashboard`, `/inbox`, `/tasks`, `/attention`, `/connections`, `/analytics`, `/settings`) — for signed-in users.

There is also **one assistant** (Kestrel/JARVIS) that floats over every dashboard screen.

```
app/
├── layout.tsx              root shell (fonts, theme, metadata)
├── page.tsx                landing page
├── globals.css             the whole design system
├── privacy/  terms/        legal pages
├── (auth)/                 login, signup, forgot/reset password
├── (dashboard)/            the app itself
└── api/auth/logout/        Next-side logout handler
components/                 all reusable UI
lib/                        API clients, helpers, brand
```

---

## 2. How the browser talks to the backend

This is the single most important thing to understand about the frontend.

**The browser does not call FastAPI directly.** It calls `/api/...` on its own origin. Next.js rewrites those requests to the backend (`next.config.ts:28-39`). This keeps the `httpOnly` session cookie on the same origin.

```
Browser  ──GET /api/messages──►  Next.js (rewrite)  ──GET {BACKEND_URL}/messages──►  FastAPI
```

### The fetch wrapper — `lib/api.ts`
Everything goes through `apiFetch<T>(path, options)`:

- Prepends `API_BASE` (default `/api`, from `NEXT_PUBLIC_API_BASE`).
- Sends `credentials: "include"` so the cookie travels.
- **GET requests are cached for 10 seconds** (`DEFAULT_TTL_MS = 10_000`) and de-duplicated while in flight — so several components asking for the same data at once make one network call.
- On **401**, it redirects to `/login` (except on auth endpoints, to avoid loops).
- On failure, it throws `ApiError` with the backend's `detail` message; a network failure becomes status `0`.
- `clearCache(path?)` invalidates cached GETs after a mutation.

There are typed modules on top of it:

| Module | Functions |
|--------|-----------|
| `lib/api/auth.ts` | `forgotPassword`, `resetPassword` |
| `lib/api/connections.ts` | `getConnections`, `createConnection`, `deleteConnection`, `getGmailAuthUrl` |
| `lib/api/tasks.ts` | `getTasks`, `completeTask`, `snoozeTask`, `getTaskMessage` |
| `lib/api/analytics.ts` | `analyticsFetch(period)` |
| `lib/api/jarvis.ts` | `jarvisChat(message, options)` |

`lib/api/server.ts` (`backendUrl()`) is **server-only** (used by the logout route) and reads `BACKEND_URL`.

---

## 3. Authentication in the UI

- **`proxy.ts`** runs as middleware. It checks whether the `cai_token` cookie is present:
  - Not present + a protected route → redirect to `/login`.
  - Present + an auth page → redirect to `/dashboard`.
- The check is **presence only**; the backend does the real validation on every API call.
- **Logout** (`components/Navbar.tsx`): disconnect realtime → `POST /api/auth/logout` → redirect to `/login`. The Next route clears the cookie even if the backend fails.
- **Hydration-safe theme:** the root layout injects an inline script that reads the saved theme and applies `.dark` **before first paint**, so there is no flash.

---

## 4. Screen-by-screen

### 4.1 Landing page — `app/page.tsx`
A hero with an animated pastel backdrop, a 4-card feature grid, and a 3-step "How it works". Uses `PublicHeader`/`PublicFooter` and `BRAND_NAME` (Sift). Buttons link to signup and the how-it-works anchor.

### 4.2 Auth pages — `app/(auth)/`
All four pages share a shell (`layout.tsx`) with a `GlassCard`, brand block, and an aurora backdrop.

- **Login:** email + password, client-side validation, `POST /auth/login`, then `router.push("/dashboard")`. "Remember me" is cosmetic.
- **Sign up:** name + email + password (min 8) + confirm; `POST /auth/register`.
- **Forgot password:** `POST /auth/forgot-password`; always shows a generic "check your inbox" message (no account enumeration).
- **Reset password:** reads `?token=` from the URL; validates 8–72 chars; `POST /auth/reset-password`.

### 4.3 Dashboard — `app/(dashboard)/dashboard/page.tsx`
The home screen after login. It fetches `/auth/me`, `/tasks`, `/messages/counts`, and `/messages`, then shows:

- A time-based greeting + name.
- Four stat cards (total messages, high priority, pending tasks, AI suggestions).
- The top 5 pending tasks with a "Done" button.
- `NeedsAttentionSection` — only messages flagged as needing attention.
- `MessageList` — recent messages.
- `SimulateMessage` — demo ingest.
- ⚠️ A temporary `BulkTestButton` block.

It refreshes when the realtime `version` changes or a local `refreshKey` changes.

### 4.4 Inbox — `app/(dashboard)/inbox/page.tsx`
The full inbox (wrapped in `Suspense` because it reads `useSearchParams`).

- **Tabs:** all / urgent / important / normal / unread (with counts).
- **Filters:** source, priority, sender, date range (`FilterBar`).
- **Search:** debounced 300 ms (`SearchBar`).
- **Message cards:** priority badge, summary, recommended action, confidence, source, time-ago, delete.
- **States:** loading skeleton, empty, error.
- **Clear inbox:** a destructive confirm dialog.

### 4.5 Tasks — `app/(dashboard)/tasks/page.tsx`
A thin server component that renders `tasks/TaskList`. The list loads `getTasks()`, shows `TaskCard`s, and supports Complete and Snooze (1 hour / tomorrow / next week) plus keyboard shortcuts.

### 4.6 Attention — `app/(dashboard)/attention/page.tsx`
Renders `NeedsAttentionSection`, which fetches `/messages`, keeps only those with `ai_analysis.needs_attention`, and shows a `NeedsAttentionCard` for each (with the "Why it matters" reason).

### 4.7 Connections — `app/(dashboard)/connections/page.tsx`
Loads connections, shows success/error banners from the `?gmail=...` query param, and renders a fixed provider catalog:

- **WhatsApp** — connect via `createConnection`.
- **Gmail** — connect via `getGmailAuthUrl()` then redirect to Google.
- **LinkedIn** — "coming soon".

Each card can disconnect (with inline confirm).

### 4.8 Analytics — `app/(dashboard)/analytics/page.tsx`
A period toggle (Today / This Week / This Month) re-fetches `analyticsFetch(period)` with no reload. Four charts (priority donut, source bars, tasks progress, trend area) are **lazy-loaded** with `next/dynamic` + `ssr:false` because recharts is heavy. Charts colour themselves from CSS variables so light/dark both stay legible.

### 4.9 Settings — `app/(dashboard)/settings/page.tsx`
Renders `SettingsClient`: Appearance (works), Profile (read-only name/email), Notifications (localStorage only), Account (no-op / disabled controls).

---

## 5. The assistant (Kestrel / JARVIS)

The assistant is mounted **once**, in `components/DashboardLayout.tsx`, so it survives navigation between dashboard routes.

```
DashboardLayout
 ├── Sidebar
 ├── Navbar
 ├── main content (RealtimeProvider-wrapped)
 └── JarvisAssistant  ← always present
      ├── JarvisLauncher (floating button)
      └── JarvisPanel (chat + orb + composer + mic)
```

### Flow of a command
1. The user types or speaks a command.
2. `JarvisAssistant.sendCommand` calls `jarvisChat(message)` → `POST /jarvis/chat`.
3. The backend returns `{reply, action, used_ai}`.
4. `localizeAssistantReply(reply)` rewrites JARVIS→Kestrel, Signal Desk→Sift.
5. If `action.type === "navigation"`, the frontend calls `router.push(action.target)`.
6. If `action.type === "request_confirmation"`, the panel shows Confirm/Cancel.
7. The reply is pushed to the transcript and **spoken** via TTS.

### Voice input — `useSpeechRecognition`
- Wraps the Web Speech API. `interimResults = true`, `continuous = false`.
- Auto-stops on the final result (so sending a command needs no explicit mic stop).
- Supports `startSilent()` (arm the mic invisibly while TTS is speaking) and `showListening()` (promote to visible listening).
- If unsupported, the UI hides the mic and offers text input only.

### Voice output — `useSpeechSynthesis`
- `cleanForSpeech()` strips markdown (code, links, headers, bullets) for speech only.
- `chunkForSpeech()` splits **only on sentence boundaries** (≤280 chars) and merges short sentences, so Chrome doesn't silently truncate a long reply.
- Chunks play **one at a time**; the next starts only after the current `onend`.
- A **session token** is bumped on every `speak()`/`stop()`; any late event from an old session is ignored.

### Barge-in
When TTS starts, the mic is silently armed. If speech activity is detected while speaking, TTS is cancelled, the orb switches to Listening, and a **generation counter** is bumped so the interrupted reply can't overwrite the new state.

---

## 6. Realtime in the UI

- `lib/realtime.ts` holds a per-tab WebSocket client with exponential backoff (1 s → 15 s) and a singleton accessor `getRealtimeClient()`.
- `components/RealtimeProvider.tsx` subscribes and exposes `useRealtime()` with a `version` number that components use as a dependency to refetch.
- If the socket can't connect, the provider falls back to polling every 15 s (`FALLBACK_POLL_MS`).
- `MessageList` additionally polls every 2.5 s **only while a message is still un-analysed**.

---

## 7. Design system

- **Tokens:** all colours live as CSS variables in `app/globals.css` (`--signal` purple, `--ember`, `--cool`, `--chart-1..5`, etc.). Components must use these variables, **never hard-coded hex**, so dark mode stays correct.
- **Utility helpers:** `.glass-card`, `.pastel-border`, `.pastel-shadow`, `.triage-label`, `.signal-lamp`.
- **Assistant orb:** `.jarvis-orb--*` classes + `jarvis-ring`/`jarvis-spin`/`jarvis-rise` keyframes.
- **UI primitives:** `components/ui/*` are shadcn "base-nova" components built on `@base-ui/react` (note: `Button` uses the base-ui `render` prop pattern, not `asChild`).
- **Icons:** lucide-react.
- **Class merging:** `cn()` from `lib/utils.ts` (clsx + tailwind-merge).

---

## 8. Types, helpers, and conventions

| File | Purpose |
|------|---------|
| `lib/brand.ts` | `BRAND_NAME`, `ASSISTANT_NAME`, `localizeAssistantReply` |
| `lib/site.ts` | `CONTACT_EMAIL`, `LEGAL_LAST_UPDATED`, `PUBLIC_LINKS` |
| `lib/priority.ts` | Priority config (only urgent/important/normal in the UI) |
| `lib/theme.tsx` | Theme provider + hook |
| `lib/time-ago.ts` / `lib/use-time-ago.ts` | Human-friendly timestamps |
| `lib/utils.ts` | `cn()` |

**Conventions to respect when editing:**
- React Compiler is ON — **do not hand-write `useCallback`/`useMemo`** in components (lint enforces `react-hooks/preserve-manual-memoization`).
- Tests must call `afterEach(cleanup)` because vitest globals are off.
- Use CSS variables for colour, not hex.

---

## 9. Frontend testing

- Runner: **vitest** + Testing Library in **jsdom** (`vitest.config.ts`).
- Test locations: `app/**/__tests__/`, `components/**/__tests__/`, `tests/**/`.
- Notable helpers: `components/__tests__/fakeWebSocket.ts` (a fake WebSocket), and fakes for `speechSynthesis`/`SpeechRecognition` in the jarvis tests.
- recharts needs a `ResizeObserver` stub (provided in the analytics test).

See `11_TESTING_AND_DEPLOYMENT.md` for the full picture.
