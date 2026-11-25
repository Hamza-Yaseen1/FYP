# 01 — File-by-File Analysis

> Every meaningful source file in the repository, explained in plain English: **what it is, what it does, and why it exists**. Paths are relative to the repo root `D:\FYP\my-app`. Line numbers refer to the state of the code at the time of analysis.

Legend: 🟦 frontend · 🟩 backend · 🟨 config/docs · ⚠️ flag (temporary, unused, or noteworthy).

---

## 1. Repository root

| File | Type | What it is / does |
|------|------|-------------------|
| `package.json` 🟨 | config | Frontend manifest. Next 16.3.1, React 19.2.8, recharts 3.10, `@base-ui/react`, lucide, tailwind-merge. Scripts: `dev`, `build`, `start`, `lint` (eslint), `test` (`vitest run`), `test:watch`. `package.json:5-12`, deps `:13-26`, devDeps `:27-41`. |
| `next.config.ts` 🟨 | config | Rewrites `/api/:path*` and `/auth/google/callback` to `BACKEND_URL` (dev fallback `http://localhost:8000`). Throws in production if `BACKEND_URL` is unset; warns in dev. Strips trailing slashes. `next.config.ts:4-25`, rewrites `:28-39`. |
| `proxy.ts` 🟦 | middleware | Route protection. Redirects unauthenticated users away from `/dashboard,/inbox,/tasks,/attention,/connections,/settings` to `/login`; redirects logged-in users away from `/login,/signup` to `/dashboard`. Checks only for the presence of the `cai_token` cookie (`proxy.ts:16`). Matcher `:34-45`. |
| `vitest.config.ts` 🟨 | config | Test runner: jsdom env, includes `app/**/*.test.ts(x)`, `components/**/*.test.tsx`, `tests/**/*.test.ts`; excludes node_modules/.next/backend/.opencode. `@` alias → repo root. `vitest.config.ts:4-14`. |
| `tsconfig.json` 🟨 | config | Strict TS, `@/*` path alias to root, Next plugin, `noEmit`. `tsconfig.json:1-33`. |
| `eslint.config.mjs` 🟨 | config | ESLint flat config extending `eslint-config-next/core-web-vitals` + `/typescript`. Ignores `.next`, `out`, `build`, `.opencode`. `eslint.config.mjs:1-17`. |
| `postcss.config.mjs` 🟨 | config | PostCSS with `@tailwindcss/postcss`. |
| `components.json` 🟨 | config | shadcn/ui config: style `base-nova`, RSC true, Tailwind CSS at `app/globals.css`, baseColor neutral, lucide icons, aliases `@/components`, `@/lib/utils`, `@/components/ui`. `components.json:1-24`. |
| `.env.example` 🟨 | config | Frontend env template: `BACKEND_URL`, `NEXT_PUBLIC_API_BASE=/api`, optional `NEXT_PUBLIC_WS_URL`, `NEXT_PUBLIC_WS_USE_TOKEN`. `.env.example:1-25`. |
| `README.md` 🟨 | docs | Marketing README. **Contains claims that overstate the code** — see `15_FINDINGS_AND_GAPS.md`. Author HAMZA YASEEN; public site `https://fyp-f8vk.vercel.app/`. |
| `AGENTS.md` 🟨 | docs | Auto-generated project guidelines + a long manual changelog of every feature phase (014–025). Useful history; see the "Recent Changes" sections. |
| `AI-FIX-SUMMARY.md` 🟨 | docs | Historical note describing an early AI failure ("Normal 0%") and the fix. **Era-stale**: refers to the OpenAI provider, which is now unused. |
| `CLAUDE.md`, `opencode.md` 🟨 | docs | Agent instruction files. |
| `SPEC.md`, `PLAN.md`, `CONSTITUTION.md`, `DEVELOPMENT_JOURNEY.md`, `WEEKLY_PROGRESS_REPORTS.md`, `SUPERVISOR_PROJECT_HIGHLIGHTS.md`, `PROJECT_AUDIT_REPORT.md`, `FIXES-APPLIED.md`, `FRONTEND-BACKEND-FIX.md`, `LOAD_TESTING_FEATURE.md`, `LOAD_TESTING_CLEANUP.md`, `QUICK-START.md`, `WEBHOOK_SETUP_GUIDE.md`, `BACKEND_EXPLAINED.md` 🟨 | docs | Supporting project documents/history. Not part of the running app. |
| `docs/day1-core-product.md` 🟨 | docs | The original product definition: 4 priority levels (Urgent/Important/Normal/Low), the "Needs Your Attention" concept, and the list of fields the AI must extract. This is the **conceptual origin** of the AI schema. `docs/day1-core-product.md:1-35`. |
| `docs/priority-agent-constitution.md`, `docs/summary-agent-delete-constitution.md` 🟨 | docs | Early per-feature "constitutions". Historical. |
| `specs/**` 🟨 | docs | Spec-kit feature specs (001-baseline, 002-priority-agent, 003-summary-delete, 011-better-inbox, 012-task-management, 013, 014, 015, 016, 017, 018, 019, 020). Historical design documents. |
| `history/**` 🟨 | docs | Recorded prompt/agent history. Historical. |
| `skills-lock.json` 🟨 | config | Lock file for the agent skills system (not app code). |

---

## 2. Frontend — `app/` (routes and layouts)

### 2.1 Root

| File | What it does |
|------|--------------|
| `app/layout.tsx` 🟦 | Root HTML shell. Loads Inter + Geist Mono fonts, sets metadata (`title = "Sift — Communication Overload Management"`, Google site-verification token), injects an inline `themeScript` that applies the saved theme **before first paint** to avoid a flash (`app/layout.tsx:29`), wraps children in `ThemeProvider`. `:19-52`. |
| `app/page.tsx` 🟦 | Public landing page. Hero with animated pastel backdrop, a 4-feature grid (`features` array `:19-40`), a 3-step "How it works" section (`steps` `:42-58`), using `PublicHeader`/`PublicFooter` and `BRAND_NAME`. Buttons link to signup/how-it-works. `:60-212`. |
| `app/globals.css` 🟦 | The entire design system. Tailwind v4 import; light (`:root` `:13-75`) and dark (`.dark` `:77-127`) token sets; `@theme inline` mapping tokens to Tailwind colors/fonts/radii (`:129-186`); drift/pan keyframes (`:188-233`); base styles + `.triage-label` + `.signal-lamp` (`:245-266`); `.pastel-border`, `.glass-card`, `.pastel-shadow` component classes (`:268-311`); the JARVIS orb styles and animations (`:313-416`). |

### 2.2 Public / legal

| File | What it does |
|------|--------------|
| `app/privacy/page.tsx` 🟦 | Full Privacy Policy page. Explains data collected, Google OAuth/Gmail scope, storage, sharing (Google/Groq/Brevo/Atlas/Vercel/Meta), retention, user rights, cookies, children's privacy, contact. Includes a `reviewNotes` array of unresolved legal questions (`:16-23`). `:25-473`. |
| `app/terms/page.tsx` 🟦 | Full Terms of Service page (13 sections). Includes the AI-limitations clause and a placeholder jurisdiction (`[jurisdiction to be confirmed — likely Pakistan...]` `:269-274`). `reviewNotes` `:16-23`. `:25-297`. |

### 2.3 Auth — `app/(auth)/`

| File | What it does |
|------|--------------|
| `app/(auth)/layout.tsx` 🟦 | Shared auth shell: aurora backdrop, theme toggle, a centered `GlassCard` with the brand block, and a "Built as Final Year Project – BBSUL" footer. `:12-46`. |
| `app/(auth)/login/page.tsx` 🟦 | Login form. Client-side validation (email regex, required password), POST `/auth/login`, on success `router.push("/dashboard")`, 401 → "Invalid email or password." `:44-69`. "Remember me" checkbox is cosmetic (unused). |
| `app/(auth)/signup/page.tsx` 🟦 | Sign-up form. Validates name/email/password (min 8 chars)/confirm, POST `/auth/register`, then `router.push("/dashboard")`. `:59-88`. |
| `app/(auth)/forgot-password/page.tsx` 🟦 | Requests a reset email via `forgotPassword(email)` → `POST /auth/forgot-password`. Always shows a generic "Check your inbox" confirmation, mentioning a 30-minute, single-use link. `:49-69`. |
| `app/(auth)/reset-password/page.tsx` 🟦 | Reads `?token=` from the URL; if missing, shows "Invalid reset link". Otherwise validates password (8–72 chars) + confirm and calls `resetPassword(token, password)` → `POST /auth/reset-password`. `:34-115`. |

### 2.4 Dashboard — `app/(dashboard)/`

| File | What it does |
|------|--------------|
| `app/(dashboard)/layout.tsx` 🟦 | Thin wrapper rendering `DashboardLayout`. `:1-5`. |
| `app/(dashboard)/dashboard/page.tsx` 🟦 | Main dashboard (client). Fetches `/auth/me`, `/tasks`, `/messages/counts`, `/messages`; shows greeting + 4 stat cards (total messages, high priority, pending tasks, AI suggestions), top-5 pending tasks with a Done button, `NeedsAttentionSection`, `MessageList`, `SimulateMessage`, and a **temporary** `BulkTestButton` block (`:269-272`). Uses `useRealtime().version` + local `refreshKey` as an `effectiveKey`. `:54-274`. |
| `app/(dashboard)/inbox/page.tsx` 🟦 | Full inbox (client, wrapped in `Suspense`). Tabs (all/urgent/important/normal/unread), `FilterBar` (source/priority/sender/date), debounced `SearchBar` (300 ms), message cards with priority badge, summary, recommended action, confidence, time-ago; empty/loading/error states; a destructive "Clear inbox" confirm dialog. Fetches `/messages/counts`, `/messages/senders`, `/messages?...`. `:71-418`. |
| `app/(dashboard)/tasks/page.tsx` 🟦 | Server component: heading + `GlassCard` wrapping `tasks/TaskList`. `:9-20`. |
| `app/(dashboard)/attention/page.tsx` 🟦 | Server component: heading + `NeedsAttentionSection` with `refreshKey={0}`. `:9-24`. |
| `app/(dashboard)/connections/page.tsx` 🟦 | Client page. Loads connections via `getConnections()`, shows success/error banners driven by the `?gmail=connected|error` query param, renders `ConnectionList`. `:8-74`. |
| `app/(dashboard)/analytics/page.tsx` 🟦 | Client page. Period state (default `week`), `analyticsFetch(period)`, lazy-loads the 4 chart components with `next/dynamic` + `ssr:false`, shows loading/error/empty/loaded states, `OverviewCards`, `SourceChart`, `TasksProgress`, `PriorityChart`, `TrendChart`. `:32-118`. |
| `app/(dashboard)/settings/page.tsx` 🟦 | Server component: heading + `SettingsClient`. `:8-18`. |

### 2.5 Next API route

| File | What it does |
|------|--------------|
| `app/api/auth/logout/route.ts` 🟦 | `POST` handler. Forwards the logout to the backend (`backendUrl("/auth/logout")`) with the `cai_token` cookie, then clears the `cai_token` cookie on the Next response (maxAge 0, httpOnly, SameSite lax). `:5-33`. |
| `app/api/auth/logout/route.test.ts` 🟦 | Unit test for the logout route. |

### 2.6 Frontend tests

| File | What it does |
|------|--------------|
| `app/(dashboard)/analytics/__tests__/page.test.tsx` 🟦 | Analytics page tests (includes a `ResizeObserver` stub for recharts). |
| `app/(dashboard)/inbox/__tests__/page.test.tsx` 🟦 | Inbox page tests. |

---

## 3. Frontend — `components/`

### 3.1 Layout & shell

| File | What it does |
|------|--------------|
| `components/DashboardLayout.tsx` 🟦 | Dashboard shell: aurora backdrop, desktop sidebar (`lg:flex`), `Navbar`, `SignalLine`, main scroll area wrapped in `RealtimeProvider`, and the always-mounted `JarvisAssistant`. `:8-34`. |
| `components/Sidebar.tsx` 🟦 | Nav list (Dashboard, Inbox, Attention, Analytics, Tasks, Connections, Settings) with active-state styling via `usePathname()`, brand block, "v1.0.0" footer. `:17-93`. |
| `components/Navbar.tsx` 🟦 | Top bar: mobile sidebar `Sheet`, global search form (pushes `/inbox?q=`), `ThemeToggle`, a decorative notification bell, and a user dropdown (email + Log out). Logout disconnects realtime, calls `/api/auth/logout`, redirects to `/login`. `:32-161`. |
| `components/SignalLine.tsx` 🟦 | Thin strip under the navbar showing "X messages in · Y important · Z need you now" from `GET /messages/counts`, with an "Action needed / All quiet" indicator. `:23-83`. |
| `components/AuroraBackdrop.tsx` 🟦 | Decorative animated pastel gradient blobs (CSS-only, `aria-hidden`, `pointer-events-none`, respects `motion-reduce`). `:8-25`. |
| `components/GlassCard.tsx` 🟦 | Presentational card wrapper (`glass` + `glow` flags) extending `div` props. `:4-25`. |

### 3.2 Inbox & messages

| File | What it does |
|------|--------------|
| `components/MessageList.tsx` 🟦 | Message feed used on the dashboard. Sorts by priority then recency, shows sender/source/unread/analyzing badges, priority badge, subject (`Re: …`), content, summary, recommended action, time-ago, delete button. Polls every 2.5 s **only while some message lacks `ai_analysis`** (cache bypass). `:67-276`. |
| `components/InboxTabs.tsx` 🟦 | Segmented tab buttons with optional count pills. `:18-57`. |
| `components/FilterBar.tsx` 🟦 | Dropdown filters for source/priority/sender + a date-range panel (From/To). "Clear filters" resets all. `:40-198`. |
| `components/SearchBar.tsx` 🟦 | Debounced search input with clear button. `:16-72`. |
| `components/PriorityBadge.tsx` 🟦 | Interactive badge: dropdown to change a message's priority via `PUT /messages/{id}/priority?priority=…`, confidence %, and "Review"/"Verify" flags. Shows "Pending" for un-analysed messages instead of "Normal 0%". `:61-172`. |
| `components/EmptyState.tsx` 🟦 | Empty/zero-result placeholder with three modes: `no-messages`, `no-results`, `no-filtered-results`. `:13-65`. |
| `components/LoadingSkeleton.tsx` 🟦 | Pulse skeleton cards. `:10-24`. |
| `components/ConfirmDialog.tsx` 🟦 | Accessible modal confirm dialog via portal; Escape-to-close; `role="alertdialog"`. `:19-69`. |
| `components/SimulateMessage.tsx` 🟦 | Form that POSTs `{sender, message}` to `/webhooks/simulate`, then `clearCache()` and calls `onSent()`. `:9-58`. |
| `components/BulkTestButton.tsx` ⚠️ | **TEMPORARY** load-testing control (comment `:1-4`) that POSTs `{count}` to `/test/bulk-messages`. Should be removed before production. `:25-112`. |

### 3.3 Tasks

| File | What it does |
|------|--------------|
| `components/tasks/TaskList.tsx` 🟦 | Loads tasks via `getTasks()`, renders `TaskCard`s, complete/snooze handlers, "View" navigates to `/inbox?messageId=…`. `:24-87`. |
| `components/tasks/TaskCard.tsx` 🟦 | Task card with priority colouring, deadline, time-ago, Complete + Snooze dropdown (1 hour / Tomorrow / Next week), View button, keyboard shortcuts (Enter/Space complete, S snooze, V view). `:55-186`. |
| `components/TaskList.tsx` ⚠️ | An **older, unused** task list (imports `timeAgo`, uses `apiFetch("/tasks")` directly and status Start/Done). Superseded by `components/tasks/TaskList.tsx`. Flag as dead code. `:34-148`. |

### 3.4 Attention

| File | What it does |
|------|--------------|
| `components/NeedsAttentionSection.tsx` 🟦 | Fetches `/messages`, filters `ai_analysis.needs_attention`, renders `NeedsAttentionCard`s with a count pill; optional empty message. `:27-88`. |
| `components/NeedsAttentionCard.tsx` 🟦 | Attention card: "Needs attention" badge, task/summary title, source icon + sender, deadline chip, "Why it matters" reason, recommended action. `:33-113`. |

### 3.5 Connections

| File | What it does |
|------|--------------|
| `components/connections/ConnectionList.tsx` 🟦 | Renders a fixed provider catalog (WhatsApp, Gmail, LinkedIn "coming soon"), merging fetched connections. `:17-31`. |
| `components/connections/ConnectionCard.tsx` 🟦 | Per-provider card. Connect: Gmail → `getGmailAuthUrl()` + redirect; others → `createConnection()`. Disconnect: inline confirm then `deleteConnection()`. Handles `connected`/`disconnected`/`error`/`coming_soon`. `:35-162`. |

### 3.6 Analytics

| File | What it does |
|------|--------------|
| `components/analytics/OverviewCards.tsx` 🟦 | 5 stat cards: Total, Urgent, Important, Normal, Low. `:11-43`. |
| `components/analytics/PeriodToggle.tsx` 🟦 | Today / This Week / This Month segmented toggle (`role="group"`, `aria-pressed`). `:17-35`. |
| `components/analytics/PriorityChart.tsx` 🟦 | recharts donut of priority distribution using CSS-var colours; returns null when empty. `:31-69`. |
| `components/analytics/SourceChart.tsx` 🟦 | recharts bar chart of counts per source. `:33-70`. |
| `components/analytics/TasksProgress.tsx` 🟦 | Donut of completed vs remaining tasks; zero-state placeholder. `:19-68`. |
| `components/analytics/TrendChart.tsx` 🟦 | recharts area chart of trends; tick formatter handles hourly (`slice(11,16)`) vs daily (`slice(5)`). `:30-73`. |

### 3.7 Settings

| File | What it does |
|------|--------------|
| `components/SettingsClient.tsx` 🟦 | Settings sections: Appearance (`AppearanceSettings`), Profile (read-only name/email from `/auth/me`), Notification prefs (localStorage-only toggles), Account management ("Sign out everywhere" no-op ⚠️, disabled "Delete account" ⚠️). `:94-198`. |
| `components/AppearanceSettings.tsx` 🟦 | Light / Dark / System theme selector. `:12-53`. |
| `components/ThemeToggle.tsx` 🟦 | Sun/Moon toggle; hydration-safe via `useSyncExternalStore`. `:12-38`. |
| `components/HealthBadge.tsx` 🟦 | Pill showing backend health via `GET /health` (connected / connecting / unavailable). `:6-43`. |

### 3.8 Assistant (Kestrel / JARVIS)

| File | What it does |
|------|--------------|
| `components/jarvis/JarvisAssistant.tsx` 🟦 | The orchestrator. Owns conversation, confirmation flow, navigation dispatch, and voice barge-in. `sendCommand` calls `jarvisChat`, `localizeAssistantReply`, pushes reply, handles `request_confirmation` vs navigation, speaks the reply. Stale-response guard via `generationRef`. Orb state derived from listening/thinking/speaking. `:14-235`. |
| `components/jarvis/JarvisPanel.tsx` 🟦 | The chat panel: header (orb + status + close), transcript, confirmation block with Confirm/Cancel, draft-reply block, composer with mic toggle and send. Auto-scrolls. `:10-234`. |
| `components/jarvis/JarvisOrb.tsx` 🟦 | Presentational status orb; maps state → CSS class; `role="status"`, `aria-live`. `:19-43`. |
| `components/jarvis/JarvisLauncher.tsx` 🟦 | Floating launcher button (bottom-right) that opens the panel. `:7-20`. |
| `components/jarvis/JarvisStatus.tsx` 🟦 | Text label per orb state ("Kestrel ready" / Listening / Thinking / Speaking). `:13-19`. |
| `components/jarvis/types.ts` 🟦 | Type-only: `JarvisOrbState`, `JarvisActionType` (13 variants), `JarvisAction`, `JarvisMessage`. `:1-29`. |
| `components/jarvis/hooks/useSpeechRecognition.ts` 🟦 | Web Speech recognition wrapper. `interimResults=true`, `continuous=false`; auto-stops on the final result; supports `startSilent()` (arm mic invisibly during TTS), `showListening()`, `toggle()` promotion. `:66-188`. |
| `components/jarvis/hooks/useSpeechSynthesis.ts` 🟦 | Chunked TTS. Exports `cleanForSpeech()` (strips markdown for speech), `chunkForSpeech()` (sentence-boundary chunking, max 280 chars), and the hook (sequential playback, session tokens to ignore stale events, unmount cleanup). `:30-253`. |

### 3.9 Assistant tests — `components/jarvis/__tests__/`

`JarvisAssistant.test.tsx`, `JarvisAssistantActions.test.tsx`, `JarvisActions.test.tsx`, `JarvisBargeIn.test.tsx`, `JarvisLauncher.test.tsx`, `JarvisMic.test.tsx`, `JarvisOrb.test.tsx`, `JarvisPanel.test.tsx`, `useSpeechRecognition.test.tsx`, `useSpeechSynthesis.test.tsx`, `jarvisApi.test.tsx` 🟦. (All call `afterEach(cleanup)` because vitest globals are off.)

### 3.10 Marketing

| File | What it does |
|------|--------------|
| `components/marketing/PublicHeader.tsx` 🟦 | Sticky public header: brand, nav (Features / How it works / Privacy / Terms), theme toggle, Sign in + Get Started. `:1-63`. |
| `components/marketing/PublicFooter.tsx` 🟦 | 4-column footer: brand, Product links, Legal links, Contact (`mailto:CONTACT_EMAIL`, "Final Year Project — BBSUL"); bottom bar with dynamic year + `LEGAL_LAST_UPDATED`. `:1-100`. |
| `components/marketing/LegalPageShell.tsx` 🟦 | Shared legal-page layout. Exports `LegalPageShell`, `LegalSection`, `LegalList`. Renders a hero, an amber "review notes" callout, the article, and a contact card. `:15-115`. |

### 3.11 UI primitives — `components/ui/`

Generated shadcn "base-nova" primitives on `@base-ui/react`:

| File | What it does |
|------|--------------|
| `button.tsx` | `Button` + `buttonVariants` (cva): variants default/outline/secondary/ghost/destructive/link; sizes xs..icon-lg. `:43-58`. Note: uses base-ui `render` prop pattern (not `asChild`). |
| `card.tsx` | `Card`, `CardHeader/Title/Description/Action/Content/Footer`. `:5-103`. |
| `badge.tsx` | `Badge` + `badgeVariants` using base-ui `useRender`. `:30-52`. |
| `input.tsx` | `Input` on base-ui input primitive. `:6-20`. |
| `label.tsx`, `separator.tsx`, `avatar.tsx`, `dropdown-menu.tsx`, `sheet.tsx` | Supporting primitives used across the app. |

### 3.12 Component tests — `components/__tests__/`

`SearchBar.test.tsx`, `RealtimeProvider.test.tsx`, `realtime.test.tsx`, `PriorityBadge.test.tsx`, `InboxTabs.test.tsx`, `FilterBar.test.tsx`, `EmptyState.test.tsx`, `fakeWebSocket.ts` (test helper) 🟦.

---

## 4. Frontend — `lib/`

| File | What it does |
|------|--------------|
| `lib/api.ts` 🟦 | The core fetch wrapper. `ApiError` class; `safeFetch` (network errors → ApiError 0); a GET-only 10 s cache + in-flight dedup; `apiFetch<T>` (credentials include, JSON, 401 → redirect to `/login` except on auth endpoints, parses `detail`); `clearCache(path?)`. `:3-187`. |
| `lib/api/config.ts` 🟦 | `API_BASE` (from `NEXT_PUBLIC_API_BASE`, default `/api`) and `apiUrl(path)`. Doc explains `/api` must stay relative so the Next rewrite proxies and keeps the httpOnly cookie. `:1-29`. |
| `lib/api/server.ts` 🟦 | Server-only `backendUrl(path)` reading `BACKEND_URL`; throws if unset or not http(s); strips trailing slashes. Non-`NEXT_PUBLIC_` on purpose. `:7-32`. |
| `lib/api/auth.ts` 🟦 | `forgotPassword(email)`, `resetPassword(token, password)`. `:3-21`. |
| `lib/api/connections.ts` 🟦 | `Connection` type + `getConnections`, `createConnection`, `deleteConnection`, `getGmailAuthUrl`. Raw fetch + `clearCache()` after mutations. `:1-95`. |
| `lib/api/tasks.ts` 🟦 | `Task`/`TaskSourceMessage` types + `getTasks`, `completeTask`, `snoozeTask`, `getTaskMessage`. `:1-117`. |
| `lib/api/analytics.ts` 🟦 | `AnalyticsPeriod`, `AnalyticsResponse`, `analyticsFetch(period="week")`. `:3-32`. |
| `lib/api/jarvis.ts` 🟦 | Re-exports `JarvisAction`; `JarvisChatResponse`, `JarvisChatOptions`, `jarvisChat(message, options)`. `:4-27`. |
| `lib/realtime.ts` 🟦 | Browser WebSocket client. `RealtimeClient` class with exponential backoff (1 s→15 s), per-tab singleton, `wsTokenEnabled()`, `fetchWsToken()`, `buildWebSocketUrl()`, `subscribe`/`subscribeStatus`. Event types `message.created`/`message.updated`. `:22-253`. |
| `lib/brand.ts` 🟦 | `BRAND_NAME = "Sift"`, `ASSISTANT_NAME = "Kestrel"`, `localizeAssistantReply()` (rewrites JARVIS/Signal Desk). `:1-9`. |
| `lib/site.ts` 🟦 | `CONTACT_EMAIL`, `LEGAL_LAST_UPDATED`, `PUBLIC_LINKS`. `:1-14`. |
| `lib/priority.ts` 🟦 | Priority config for **urgent/important/normal** (emoji/colour/bg) + `getPriorityConfig/Emoji/Color`. Note: the type omits `low`/`pending` even though the backend uses them. `:1-40`. |
| `lib/theme.tsx` 🟦 | `Theme` type, `ThemeProvider`, `useTheme()`; localStorage persistence, system-preference subscription via `useSyncExternalStore`, toggles `.dark` on `<html>`. `:1-92`. |
| `lib/time-ago.ts` 🟦 | `parseApiDate()` (appends `Z` when no timezone) and `timeAgo()`. `:1-26`. |
| `lib/use-time-ago.ts` 🟦 | Hook wrapping `timeAgo` with a 30 s refresh interval. `:6-21`. |
| `lib/utils.ts` 🟦 | `cn()` = clsx + tailwind-merge. `:4-6`. |

---

## 5. Backend — root (`backend/`)

| File | What it does |
|------|--------------|
| `backend/main.py` 🟩 | FastAPI app. Lifespan: connects to Mongo, creates indexes (users.email unique, users.reset_token_hash sparse, messages user_id+created_at, messages text index, drops the legacy global dedupe index), starts the Gmail poller (if `GOOGLE_CLIENT_ID` set and not on the test DB) and the pending-retry sweep. Adds GZip + CORS. Registers routers: auth, messages, webhooks, tasks, connections, gmail+google, analytics, jarvis, ws. |
| `backend/database.py` 🟩 | Motor async client with pinned DNS resolvers (8.8.8.8/1.1.1.1/8.8.4.4), `tz_aware=True`, timeouts. Exposes `MONGO_URI`, `DB_NAME`, collections (`messages`, `users`, `ai_analysis`, `tasks`, `connections`) and `create_indexes()` for tasks. |
| `backend/dependencies.py` 🟩 | `get_current_user`: reads `cai_token` cookie → `decode_token` → validates ObjectId → loads user, else 401. |
| `backend/requirements.txt` 🟩 | Runtime deps: fastapi, uvicorn[standard], pydantic, motor, python-dotenv, groq, openai, bcrypt, cryptography, PyJWT, email-validator, httpx; dev: pytest. |
| `backend/.env.example` 🟩 | Backend env template (Mongo, Groq, OpenAI optional, JWT_SECRET, ENCRYPTION_KEY, WhatsApp, Brevo, Google OAuth, poll/retry, WS). `:1-80`. |
| `backend/check_models.py` ⚠️ | Utility that lists Groq models via REST. Dev-only. |
| `backend/test_ai_analysis.py`, `backend/test_task_extraction.py`, `backend/test_priority_integration.py`, `backend/test_priority_edge_cases.py`, `backend/test_attention_pipeline.py` ⚠️ | **Era-stale root-level standalone scripts** (not in the maintained pytest suite). Some need a live server/secrets. Kept as historical artifacts — do not chase their failures. |

### 5.1 `backend/utils/`

| File | What it does |
|------|--------------|
| `backend/utils/encryption.py` 🟩 | AES token encryption helpers (`encrypt`/`decrypt`) using `ENCRYPTION_KEY`. Used for Gmail OAuth tokens. **Note:** there is **no `utils/__init__.py`** (imported as a namespace package). |

### 5.2 `backend/models/`

| File | What it does |
|------|--------------|
| `backend/models/user.py` 🟩 | User schemas (`UserCreate`, `UserLogin`, `UserResponse`, etc.). |
| `backend/models/message.py` 🟩 | `RoutingRecord`, `AIAnalysis` (status default `pending`, provider default `unknown`), `ContextUpdate`, `MessageCreate`, `SimulateMessageRequest`, `MessageUpdate`, `MessageResponse`. |
| `backend/models/task.py` 🟩 | `ExtractedTask`, `TaskResponse`. |
| `backend/models/connection.py` 🟩 | `Provider` enum (whatsapp/gmail/linkedin), `ConnectionStatus` enum (connected/disconnected/error/coming_soon). |
| `backend/models/meta_webhook.py` 🟩 | Pydantic shapes for the Meta WhatsApp webhook payload. |
| `backend/models/__init__.py` 🟩 | Empty package marker. |

### 5.3 `backend/routes/`

| File | Endpoints | What it does |
|------|-----------|--------------|
| `backend/routes/auth.py` 🟩 | `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`, `POST /auth/forgot-password`, `POST /auth/reset-password` | Registration (409 on duplicate), bcrypt hashing, sets the session cookie via `_set_session_cookie`, generic forgot-password response, reset validation. |
| `backend/routes/messages.py` 🟩 | `GET /messages`, `GET /messages/counts`, `GET /messages/senders`, `POST /messages`, `DELETE /messages`, `DELETE /messages/{id}`, `PUT /messages/{id}/priority`, `POST /messages/{id}/reanalyze` | Listing with tabs/filters/search/pagination; counts and senders; create (runs the orchestrator); clear inbox; delete; priority override; re-analyze. All user-scoped. |
| `backend/routes/webhooks.py` 🟩 | `GET /webhooks/whatsapp` (verify), `POST /webhooks/whatsapp`, `POST /webhooks/simulate` | Meta verification challenge; HMAC `X-Hub-Signature-256` verification; parse text messages; ingest via `webhook_ingest`; simulate path (background analysis, `ai_analysis: null` on response). Imports `get_current_user` from `routes.auth`. |
| `backend/routes/gmail.py` 🟩 | `GET /connections/gmail/auth-url`, `GET /connections/gmail/callback`, `GET /auth/google/callback`, `POST /connections/gmail/refresh` | Starts OAuth (auth-gated), handles callback (never auth-gated; state binds user), alias callback, forced full INBOX resync. |
| `backend/routes/connections.py` 🟩 | `GET /connections`, `POST /connections`, `DELETE /connections/{id}` | List/create/delete connections. Gmail creation via this endpoint is rejected (must use OAuth). Disconnect revokes Google token best-effort then deletes. |
| `backend/routes/tasks.py` 🟩 | `GET /tasks`, `PUT /tasks/{id}/status`, `PUT /tasks/{id}/snooze`, `GET /tasks/{id}/message` | List (excludes completed + currently snoozed; priority-sorted then recency; limit 100), complete, snooze (1hour/tomorrow/nextweek), fetch source message. |
| `backend/routes/analytics.py` 🟩 | `GET /analytics?period=day|week|month` | Validates period (400 otherwise) and returns `build_analytics_response`. |
| `backend/routes/jarvis.py` 🟩 | `POST /jarvis/chat` | The assistant endpoint. Auth-gated; empty/missing message → 400; returns `{reply, action, used_ai}`. Owner id always from the session. |
| `backend/routes/ws.py` 🟩 | `GET /ws`, `GET /ws-token` | WebSocket auth (cookie, or dev `?token=` fallback gated by `WS_ALLOW_QUERY_TOKEN`), registers with `realtime`; inbound text ignored (keep-alive). `/ws-token` mints a short-lived WS token. |
| `backend/routes/__init__.py` 🟩 | — | Empty package marker. |

### 5.4 `backend/services/`

| File | What it does |
|------|--------------|
| `backend/services/security.py` 🟩 | `hash_password`/`verify_password` (bcrypt), `create_access_token`, `decode_token` (rejects tokens carrying a `purpose`), `create_ws_token`/`decode_ws_token`. Raises if `JWT_SECRET` unset. |
| `backend/services/connection.py` 🟩 | `ConnectionService` for connection CRUD; encrypts tokens via `utils/encryption`. |
| `backend/services/gmail.py` 🟩 | Google OAuth helpers + inbox poller. Auth URL, signed state (JWT), token exchange/refresh/revoke, `normalize_email` (MIME parse, HTML fallback, attachments skipped), `_clean_sender`, poller with `after:<epoch>` watermark. |
| `backend/services/password_reset.py` 🟩 | Reset token creation (only SHA-256 hash stored), TTL 30 min, single-use, 60 s cooldown, generic response; sends email via Brevo REST (`https://api.brevo.com/v3/smtp/email`). |
| `backend/services/analytics.py` 🟩 | `build_analytics_response` + `VALID_PERIODS`, `PERIOD_DAYS`, `PRIORITY_BUCKETS`. Every pipeline starts with a `user_id` `$match`; 5 concurrent reads via `asyncio.gather`; UTC windows; zero-filled trends. |
| `backend/services/realtime.py` 🟩 | `ConnectionManager` mapping `user_id → set[WebSocket]`; `MESSAGE_CREATED`/`MESSAGE_UPDATED`; per-user fan-out; best-effort send with 2 s timeout; dead-socket pruning. |
| `backend/services/retry_pending.py` 🟩 | `retry_pending_analyses` / `reanalyze_user_pending`: re-enters the SAME `process_message` (never `analyze_message`), user-scoped `$set`, idempotent, sequential with sleep + max-consecutive-failure stop. |
| `backend/services/threads.py` 🟩 | `resolve_and_stamp`: deterministic thread linking (same user + source + normalized sender, within `LINK_WINDOW_MINUTES=60`); `threadId` = anchor `_id` minted on the 2nd in-window message. |
| `backend/services/webhook_ingest.py` 🟩 | `ingest_message`: the shared ingest path for all sources. Dedupe, thread stamping, insert, and (when no background task) spawns `_analyze_and_store` via `process_message`. |
| `backend/services/__init__.py` 🟩 | Re-exports `analyze_message`. |

### 5.5 `backend/services/ai/`

| File | What it does |
|------|--------------|
| `backend/services/ai/__init__.py` 🟩 | Re-exports `analyze_message`, `process_message`. |
| `backend/services/ai/orchestrate.py` 🟩 | The **single AI entry point** `process_message`: rule-based routing → trivial/no-content short-circuit (zero LLM) → one combined analysis call → gate outputs → attach the explainable `routing` record. `_analyze_with_fallback` guards crashes. |
| `backend/services/ai/routing.py` 🟩 | Pure deterministic `decide_routing`. `AGENT_IDS` = priority, summary, task_extraction, deadline_detection, recommended_action. `TASK_TRIGGER_KEYWORDS`, `TIME_EXPRESSION_KEYWORDS`; fail-toward-completeness default. |
| `backend/services/ai/analyzer.py` 🟩 | `analyze_message` — builds the prompt, calls the provider, parses the JSON, maps to `AIAnalysis`. `TOO_LARGE_EXPLANATION` is a terminal failure state. |
| `backend/services/ai/attention.py` 🟩 | Pure `evaluate_attention`: R1 (task + near-term deadline), R2 (urgent + task); `NEAR_TERM_KEYWORDS`. |
| `backend/services/ai/token_budget.py` 🟩 | Token estimation (~4 chars/token), `budget_message`, `budget_context_messages`, `TRUNCATION_MARKER`; keeps the `Subject:` line; short messages unchanged. |
| `backend/services/ai/context.py` 🟩 | Thread context: `fetch_thread_context` (≤5 same-user, excludes current), `build_context_block`, `validate_context_updates` (only verbatim values from a provable source), `apply_context_updates` ($push-only, user-scoped). |
| `backend/services/ai/jarvis_agent.py` 🟩 | The assistant's single entry `process_command(user_id, message)`. Layered dispatch: Phase 4 (messages) → Phase 2 (actions) → Phase 3 (intents) → Phase 1 (routing) → Phase 5 (conversation/context). `_handle_chat` uses `GroqProvider.chat()` only when configured; otherwise deterministic fallbacks. All data fetchers user-scoped. |
| `backend/services/ai/jarvis_intents.py` 🟩 | Phase 3 NLU. `detect_intent` (deterministic superset of Phase 1 nav/info), `llm_info_intent` (optional Groq label, whitelist-only, called only when routing said unknown). `NAV_TARGETS`/`NAV_VERBS` live here. |
| `backend/services/ai/jarvis_actions.py` 🟩 | Phase 2 actions. `CONFIRM_TTL_MINUTES=2`, signed confirmation tokens (`CONFIRM_PURPOSE="jarvis_confirm"`), `request_confirmation` for create/delete task, complete task, message search, summarize, important list, completed-task list, attention, draft reply. |
| `backend/services/ai/jarvis_messages.py` 🟩 | Phase 4 message intelligence. `detect_message_intent` (pure) + `run_message_intent`. 8 intents (count, today list, yesterday, by-date, list, summarize, important, urgent). Ownership rules keep earlier phases byte-identical. Groq used only for summarize, on a digest of the user's own messages. |
| `backend/services/ai/providers/base.py` 🟩 | `AIAnalysisResult` dataclass + `BaseLLMProvider.analyze(message, context, current_message_id)`. |
| `backend/services/ai/providers/groq.py` 🟩 | The active provider. `MODEL_NAME` (default `qwen/qwen3.8-27b`), `FALLBACK_MODEL` (`openai/gpt-oss-20b`), `MAX_OUTPUT_TOKENS=400`, `reasoning_effort="none"`, JSON response format, retries for transient errors, a circuit breaker for daily-quota (TPD) 429s, a one-shot 413 fallback, concurrency cap, and a private `chat()` for JARVIS. |
| `backend/services/ai/providers/openai.py` ⚠️ | An OpenAI provider that exists but is **unused** (the factory always returns Groq). Historical (see `AI-FIX-SUMMARY.md`). |
| `backend/services/ai/providers/__init__.py` 🟩 | Exports `BaseLLMProvider`, `OpenAIProvider`. |
| `backend/services/ai/prompts/priority.txt` 🟩 | Priority + task extraction prompt (4 levels; task fields). |
| `backend/services/ai/prompts/tasks.txt` 🟩 | Task-extraction rules (deadline discipline: never invent dates). |
| `backend/services/ai/prompts/summary.txt` 🟩 | Summary prompt (1–2 sentences, <30 words). |
| `backend/services/ai/prompts/actions.txt` 🟩 | Recommended-action prompt (single imperative; matches message language incl. Arabic examples). |

### 5.6 `backend/scripts/` ⚠️ (operational / dev only)

| File | What it does |
|------|--------------|
| `backend/scripts/assign_legacy_data.py` | Assigns messages/tasks missing `user_id` to a user by email. Idempotent. |
| `backend/scripts/setup_whatsapp_connection.py` | Creates a WhatsApp connection for the first user (needed so the webhook can route messages). |
| `backend/scripts/setup_connection_indexes.py` | Creates the `connections` unique `(user_id, provider)` index. |
| `backend/scripts/test_webhook.py` | Prints a webhook setup health check (connection present, env vars, recent messages). |
| `backend/scripts/simulate_meta_webhook.py` | Signs and POSTs a realistic Meta webhook payload to `localhost:8000/webhooks/whatsapp`. |

### 5.7 `backend/tests/`

The maintained pytest suite. `conftest.py` sets `DB_NAME=communication_ai_test`, loads `.env`, exposes a session `TestClient` and an autouse `clean_db` fixture that wipes users/messages/tasks/connections around every test. See `11_TESTING_AND_DEPLOYMENT.md` for the full breakdown.

---

## 6. Summary of flags (things to fix or explain)

| Flag | File(s) | Why |
|------|---------|-----|
| TEMPORARY load-testing UI | `components/BulkTestButton.tsx`, `app/(dashboard)/dashboard/page.tsx:269-272` | Should be removed before production. |
| Dead/duplicate task list | `components/TaskList.tsx` | Superseded by `components/tasks/TaskList.tsx`; not imported anywhere. |
| Unused provider | `backend/services/ai/providers/openai.py` | Kept for history; the factory never selects it. |
| No-op settings controls | `components/SettingsClient.tsx` ("Sign out everywhere", "Delete account") | Presentational only. |
| Era-stale scripts | `backend/test_*.py` (5 files), `AI-FIX-SUMMARY.md` | Reference the old OpenAI flow; not part of the suite. |
| Brand rename in progress | `lib/brand.ts`, all `jarvis*` files | JARVIS/Signal Desk → Kestrel/Sift at display time. |
| Missing `utils/__init__.py` | `backend/utils/` | Works as a namespace package; add a marker if packaging. |
| README overstates features | `README.md` | See `15_FINDINGS_AND_GAPS.md` for the full list. |
