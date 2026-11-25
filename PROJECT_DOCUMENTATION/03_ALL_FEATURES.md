# 03 — All Features

> A complete, honest inventory of every feature in Sift: **what it does**, **where it lives in the code**, **its status**, and **its limitations**. Statuses: ✅ Implemented · 🟡 Partial · 🔵 Planned / placeholder · ⚠️ Temporary / remove.

---

## Feature index

| # | Feature | Status |
|---|---------|--------|
| F01 | Account registration & login | ✅ |
| F02 | Session management (JWT cookie) | ✅ |
| F03 | Logout | ✅ |
| F04 | Password reset by email | ✅ |
| F05 | Route protection | ✅ |
| F06 | Public landing page | ✅ |
| F07 | Privacy Policy & Terms pages | ✅ |
| F08 | Dark / light / system theme | ✅ |
| F09 | Dashboard overview | ✅ |
| F10 | Inbox with tabs | ✅ |
| F11 | Inbox filters (source/priority/sender/date) | ✅ |
| F12 | Inbox search | ✅ |
| F13 | Clear inbox | ✅ |
| F14 | Delete a message | ✅ |
| F15 | Manual priority override | ✅ |
| F16 | Re-analyze a message | ✅ |
| F17 | Message simulation (demo ingest) | ✅ |
| F18 | WhatsApp webhook ingestion | ✅ |
| F19 | Gmail OAuth ingestion | ✅ |
| F20 | Connection management UI | ✅ |
| F21 | AI priority classification | ✅ |
| F22 | AI summary | ✅ |
| F23 | AI recommended action | ✅ |
| F24 | AI task extraction | ✅ |
| F25 | AI deadline detection | ✅ |
| F26 | "Needs your attention" | ✅ |
| F27 | Explainable AI routing record | ✅ |
| F28 | AI failure handling & retry | ✅ |
| F29 | Thread linking (deterministic) | ✅ |
| F30 | AI thread context memory | ✅ |
| F31 | Task list | ✅ |
| F32 | Complete / snooze tasks | ✅ |
| F33 | Analytics (day/week/month) | ✅ |
| F34 | Realtime updates | ✅ |
| F35 | Assistant — navigation | ✅ |
| F36 | Assistant — real-data info | ✅ |
| F37 | Assistant — message intelligence | ✅ |
| F38 | Assistant — actions (task create/complete/delete) | ✅ |
| F39 | Assistant — confirmation flow | ✅ |
| F40 | Assistant — conversation & follow-ups | ✅ |
| F41 | Assistant — voice input (speech recognition) | ✅ |
| F42 | Assistant — voice output (chunked TTS) | ✅ |
| F43 | Assistant — voice barge-in | ✅ |
| F44 | Bulk load testing | ⚠️ TEMPORARY |
| F45 | Settings (appearance / profile / notifications) | 🟡 |
| F46 | Health badge | ✅ |
| F47 | Email notifications | 🔵 |
| F48 | Sign in with Google | 🔵 (does not exist) |
| F49 | AI-drafted replies sent to others | 🔵 (draft only) |
| F50 | Delete account / sign out everywhere | 🔵 (no-op) |
| F51 | LinkedIn integration | 🔵 ("coming soon") |
| F52 | Sentiment / intent analysis (separate) | 🔵 (does not exist) |

---

## F01 — Account registration & login ✅
- **What:** Users create an account with name/email/password and log in.
- **Where:** `app/(auth)/signup/page.tsx`, `app/(auth)/login/page.tsx`, `backend/routes/auth.py`.
- **How:** `POST /auth/register` (409 on duplicate email) and `POST /auth/login` (bcrypt verify). Passwords are hashed with bcrypt; the plaintext never touches the DB.
- **Limitations:** no email verification; no OAuth login; no password strength beyond min 8 chars.

## F02 — Session management ✅
- **What:** After login, the user stays signed in without re-entering credentials.
- **Where:** `backend/services/security.py` (`create_access_token`), `_set_session_cookie` in `backend/routes/auth.py`, `proxy.ts`, `backend/dependencies.py`.
- **How:** HS256 JWT in an `httpOnly` cookie `cai_token`, 7-day expiry; `Secure`/`SameSite` env-driven. `decode_token` rejects any token carrying a `purpose` claim (so reset/WS tokens can't act as sessions).
- **Limitations:** no refresh-token rotation; logout doesn't invalidate the token server-side (stateless).

## F03 — Logout ✅
- **What:** Ends the session.
- **Where:** `components/Navbar.tsx` (client), `app/api/auth/logout/route.ts` (Next route), `backend/routes/auth.py` (`POST /auth/logout`).
- **How:** The Next route forwards to the backend and then clears the cookie on the Next response even if the backend call fails.
- **Limitations:** token remains valid until expiry if copied elsewhere (stateless JWT).

## F04 — Password reset by email ✅
- **What:** "Forgot password?" emails a single-use, 30-minute reset link.
- **Where:** `backend/services/password_reset.py`, `backend/routes/auth.py`, `app/(auth)/forgot-password/page.tsx`, `app/(auth)/reset-password/page.tsx`.
- **How:** A random token is generated; **only its SHA-256 hash is stored**; a 60-second cooldown prevents email flooding (a second request in the window reuses the original token); responses are generic to avoid account enumeration; email sent via Brevo REST.
- **Limitations:** Brevo live delivery is **unverified** in this repo (key type + sender). If email fails, the user gets no feedback.

## F05 — Route protection ✅
- **What:** Only logged-in users can reach the app; logged-in users skip auth pages.
- **Where:** `proxy.ts`.
- **How:** Checks for the presence of the `cai_token` cookie and redirects accordingly.
- **Limitations:** cookie *presence* only (the backend still enforces real validation). `/` is always public.

## F06 — Public landing page ✅
- **What:** Marketing page explaining the product with feature grid and "how it works".
- **Where:** `app/page.tsx`, `components/marketing/*`.
- **Limitations:** static; no pricing/FAQ sections.

## F07 — Privacy Policy & Terms ✅
- **What:** Full legal pages covering data handling, the Gmail scope, third parties, retention, and AI limitations.
- **Where:** `app/privacy/page.tsx`, `app/terms/page.tsx`, `components/marketing/LegalPageShell.tsx`.
- **Limitations:** several facts are placeholders (jurisdiction, retention periods) — see `15_FINDINGS_AND_GAPS.md`. The pages include an explicit "review notes" callout listing these.

## F08 — Dark / light / system theme ✅
- **What:** Theme switching with no flash on load.
- **Where:** `lib/theme.tsx`, `components/ThemeToggle.tsx`, `components/AppearanceSettings.tsx`, pre-paint script in `app/layout.tsx:29`.
- **How:** localStorage + system-preference subscription; toggles `.dark` on `<html>`; an inline script applies the theme before first paint.

## F09 — Dashboard overview ✅
- **What:** Landing screen after login: greeting, 4 stat cards, top pending tasks, attention section, recent messages, simulate control.
- **Where:** `app/(dashboard)/dashboard/page.tsx`.
- **Limitations:** includes the temporary `BulkTestButton` block.

## F10 — Inbox with tabs ✅
- **What:** A full message inbox with tabs (all / urgent / important / normal / unread) and count pills.
- **Where:** `app/(dashboard)/inbox/page.tsx`, `components/InboxTabs.tsx`.
- **Limitations:** no pagination UI beyond what the page loads; no bulk select.

## F11 — Inbox filters ✅
- **What:** Filter by source (Gmail/WhatsApp), priority, sender, and a date range.
- **Where:** `components/FilterBar.tsx`, backend filters in `backend/routes/messages.py`.
- **Limitations:** filter state is not persisted across reloads.

## F12 — Inbox search ✅
- **What:** Free-text search across sender/content/summary.
- **Where:** `components/SearchBar.tsx` (300 ms debounce), backend text index (`main.py`).
- **Limitations:** simple text index; no ranking/typo tolerance.

## F13 — Clear inbox ✅
- **What:** Deletes all messages for the user (with a confirm dialog).
- **Where:** `app/(dashboard)/inbox/page.tsx`, `DELETE /messages`.
- **Limitations:** irreversible; scoped to the user.

## F14 — Delete a message ✅
- **What:** Deletes a single message.
- **Where:** `components/MessageList.tsx`, `DELETE /messages/{id}`.
- **Limitations:** linked tasks are not cascaded (they remain, resolved via source message fallback).

## F15 — Manual priority override ✅
- **What:** The user can correct the AI's priority from a dropdown on the badge.
- **Where:** `components/PriorityBadge.tsx`, `PUT /messages/{id}/priority`.
- **How:** Stores the override and records `reviewed`/`verified` flags; the UI shows "Review"/"Verify".

## F16 — Re-analyze a message ✅
- **What:** Re-runs AI analysis on demand.
- **Where:** `POST /messages/{id}/reanalyze`.
- **Limitations:** requires the message content; media-only messages short-circuit.

## F17 — Message simulation ✅
- **What:** A demo form that injects a fake message to showcase the pipeline.
- **Where:** `components/SimulateMessage.tsx`, `POST /webhooks/simulate`.
- **How:** Runs analysis as a background task so the response returns immediately.

## F18 — WhatsApp webhook ingestion ✅
- **What:** Real WhatsApp messages flow in via Meta's webhook.
- **Where:** `backend/routes/webhooks.py`, `backend/services/webhook_ingest.py`, `backend/models/meta_webhook.py`.
- **How:** `GET` handles the verification challenge; `POST` verifies the `X-Hub-Signature-256` HMAC (constant-time) before parsing text messages.
- **Limitations:** only text messages are ingested; media is skipped. Requires a public URL + Meta app configuration.

## F19 — Gmail OAuth ingestion ✅
- **What:** Connects a Gmail inbox (read-only) and pulls new mail.
- **Where:** `backend/services/gmail.py`, `backend/routes/gmail.py`, `backend/routes/connections.py`.
- **How:** Official Google OAuth 2.0 via REST (no SDK); signed `state` JWT; encrypted tokens; `gmail.readonly` scope only; background poller with an `after:` watermark.
- **Limitations:** Google "restricted scope" → production use needs Google verification (and likely CASA). Attachments skipped.

## F20 — Connection management UI ✅
- **What:** Connect/disconnect Gmail and WhatsApp; LinkedIn shown as "coming soon".
- **Where:** `app/(dashboard)/connections/page.tsx`, `components/connections/*`.
- **Limitations:** WhatsApp connect is not a full in-app flow (it depends on the webhook configuration); LinkedIn is a placeholder.

## F21–F25 — AI analysis (priority, summary, action, tasks, deadlines) ✅
- **What:** Every message is classified and enriched by the AI.
- **Where:** `backend/services/ai/orchestrate.py`, `analyzer.py`, `routing.py`, `prompts/*.txt`, `backend/models/message.py` (`AIAnalysis`).
- **How:** One combined Groq call returns priority, summary, recommended action, tasks, and deadlines. Prompt files enforce discipline (e.g. never invent dates).
- **Limitations:** single LLM call (not multi-agent); quality depends on the model; Arabic/mixed-language input is supported but not deeply tested.

## F26 — "Needs your attention" ✅
- **What:** A focused view of messages that genuinely need a human.
- **Where:** `backend/services/ai/attention.py`, `components/NeedsAttentionSection.tsx`, `components/NeedsAttentionCard.tsx`.
- **How:** Deterministic rules: **R1** = has a task **and** a near-term deadline; **R2** = urgent **and** has a task. The reason is stored and shown ("Why it matters").
- **Limitations:** rule-based only; no user-tunable thresholds.

## F27 — Explainable AI routing record ✅
- **What:** Stores *why* the AI did what it did.
- **Where:** `backend/services/ai/orchestrate.py`, `RoutingRecord` in `backend/models/message.py`.
- **How:** Every analysis path attaches `{agents_requested, agents_run, skipped, llm_call_used, reasons}`.

## F28 — AI failure handling & retry ✅
- **What:** If the AI is unavailable, messages are marked `pending` and retried later instead of silently failing.
- **Where:** `backend/services/retry_pending.py`, `backend/services/ai/providers/groq.py` (circuit breaker), `main.py` lifespan.
- **How:** Pending sweep every 60 s re-enters `process_message`; the Groq provider has retries, a cooldown for daily-quota 429s, and a one-shot 413 fallback.
- **Limitations:** in-process (no external queue); terminal failures (message too large) are not retried.

## F29 — Thread linking (deterministic) ✅
- **What:** Related messages are grouped into a conversation.
- **Where:** `backend/services/threads.py`.
- **How:** Same user + same source + same normalized sender within 60 minutes; `threadId` = anchor message `_id`, minted on the 2nd in-window message.
- **Limitations:** **not** AI-based — subjects/Re: lines are not used; a 61-minute reply starts a new thread.

## F30 — AI thread context memory ✅
- **What:** Later messages in a thread are analysed with awareness of earlier ones.
- **Where:** `backend/services/ai/context.py`, integrated in `analyze_message`/`process_message`.
- **How:** Up to 5 prior same-user messages are fetched and rendered as a CONTEXT block; the model may propose `context_updates`, but only **verbatim** values from a provable source are accepted.
- **Limitations:** only within a deterministic thread; only 5 messages; no cross-thread memory.

## F31 — Task list ✅
- **What:** A list of tasks extracted from messages.
- **Where:** `app/(dashboard)/tasks/page.tsx`, `components/tasks/TaskList.tsx`, `GET /tasks`.
- **How:** Excludes completed and currently-snoozed tasks; sorted by priority then recency; limit 100.
- **Limitations:** tasks cannot be created manually from the UI (only via the assistant or extraction).

## F32 — Complete / snooze tasks ✅
- **What:** Mark a task done, or snooze it for 1 hour / tomorrow / next week.
- **Where:** `components/tasks/TaskCard.tsx`, `PUT /tasks/{id}/status`, `PUT /tasks/{id}/snooze`.
- **Limitations:** no recurring tasks; snooze is fixed to three presets.

## F33 — Analytics ✅
- **What:** Charts for day/week/month: totals, priority split, sources, tasks progress, trend.
- **Where:** `app/(dashboard)/analytics/page.tsx`, `components/analytics/*`, `backend/services/analytics.py`, `GET /analytics`.
- **How:** Read-only aggregation from live data, never stored; every pipeline starts with a `user_id` `$match`; UTC windows; zero-filled trends.
- **Limitations:** only three periods (the README's "7/30/90 days" is wrong); no custom range; no export.

## F34 — Realtime updates ✅
- **What:** New/updated messages appear without a manual refresh.
- **Where:** `backend/services/realtime.py`, `backend/routes/ws.py`, `lib/realtime.ts`, `components/RealtimeProvider.tsx`.
- **How:** Per-user WebSocket fan-out (`message.created`/`message.updated`); exponential backoff reconnect; a 15 s polling fallback.
- **Limitations:** in-process only (won't work across multiple backend instances); dev `?token=` path is off in production.

## F35 — Assistant navigation ✅
- **What:** "Go to inbox", "open tasks", "show analytics" moves the user to a screen.
- **Where:** `backend/services/ai/jarvis_agent.py`, `jarvis_intents.py` (`NAV_TARGETS`/`NAV_VERBS`), `components/jarvis/JarvisAssistant.tsx`.
- **How:** Deterministic matching; the backend returns an `action` and the frontend calls `router.push(action.target)`.

## F36 — Assistant real-data info ✅
- **What:** Answers about the user's own data: unread count, pending tasks, attention, dashboard summary, today's messages.
- **Where:** `jarvis_agent.py`, `jarvis_intents.py` (GET_TODAYS_MESSAGES / GET_UNREAD_MESSAGES / GET_PENDING_TASKS / GET_ATTENTION / GET_DASHBOARD_SUMMARY).
- **How:** User-scoped DB reads; deterministic replies; UTC day boundaries.

## F37 — Assistant message intelligence ✅
- **What:** Answers content questions: counts, listings by date, important/urgent, summaries.
- **Where:** `backend/services/ai/jarvis_messages.py`.
- **How:** 8 intents (count, today list, yesterday, by-date, list, summarize, important, urgent); summarize uses Groq on a digest of the user's own messages; every other intent is deterministic.
- **Limitations:** the AI summary covers at most 10 messages, content truncated to 160 chars; ownership rules mean some phrasings fall through to other phases by design.

## F38 — Assistant actions ✅
- **What:** Create, complete, and delete tasks; list important messages; search; summarize; explain attention; draft a reply.
- **Where:** `backend/services/ai/jarvis_actions.py`.
- **How:** Deterministic matchers; mutations return a `request_confirmation` action first.
- **Limitations:** draft reply is shown in the panel only — there is **no send**.

## F39 — Assistant confirmation flow ✅
- **What:** Destructive actions require an explicit Confirm.
- **Where:** `jarvis_actions.py` (`CONFIRM_TTL_MINUTES=2`, signed confirmation token), `components/jarvis/JarvisPanel.tsx`.
- **How:** The backend issues an HS256 token bound to the user; the frontend shows Confirm/Cancel and replays with `confirmed=true` + token. Tokens expire in 2 minutes.

## F40 — Assistant conversation & follow-ups ✅
- **What:** General questions get natural answers; follow-ups like "what about those?" work.
- **Where:** `jarvis_agent.py` (`_handle_chat`, `_CONTEXTS`), `jarvis_messages.py` (`resolve_message_follow_up`).
- **How:** Unknown/general commands route through `GroqProvider.chat()` **only if** `GROQ_API_KEY` is set; otherwise a deterministic "conversation unavailable" reply. Per-user in-memory context (last 8 turns) enables follow-ups and corrections. History is text-only — no DB data or user ids are ever injected into the prompt.
- **Limitations:** context is in-memory (lost on restart) and not shared across instances; conversational quality depends on the provider.

## F41 — Assistant voice input ✅
- **What:** Speak commands instead of typing.
- **Where:** `components/jarvis/hooks/useSpeechRecognition.ts`.
- **How:** Web Speech API (`SpeechRecognition`), interim results, auto-stop on final result. If unsupported, the UI falls back to text only.
- **Limitations:** browser-dependent (best in Chrome); requires microphone permission; no server-side speech-to-text.

## F42 — Assistant voice output ✅
- **What:** The assistant speaks its replies.
- **Where:** `components/jarvis/hooks/useSpeechSynthesis.ts`.
- **How:** `cleanForSpeech()` strips markdown; `chunkForSpeech()` splits on sentence boundaries (≤280 chars); chunks play sequentially, one at a time, to avoid Chrome truncating a single long utterance.
- **Limitations:** browser voice quality varies; must not be in a background/limited tab; jsdom has no `speechSynthesis` (tests use a fake).

## F43 — Assistant voice barge-in ✅
- **What:** Start talking while the assistant is speaking to interrupt it.
- **Where:** `components/jarvis/JarvisAssistant.tsx`, both speech hooks.
- **How:** TTS `onStart` silently arms the mic; speech activity cancels TTS, promotes to "Listening", and bumps a generation counter so the interrupted reply can't resurrect itself.

## F44 — Bulk load testing ⚠️
- **What:** Generates many fake messages to stress the system.
- **Where:** `components/BulkTestButton.tsx`, `POST /test/bulk-messages`.
- **Status:** **TEMPORARY** — the file header says so; remove before production.

## F45 — Settings 🟡
- **What:** Appearance, Profile, Notifications, Account sections.
- **Where:** `components/SettingsClient.tsx`, `components/AppearanceSettings.tsx`.
- **Status:** Appearance and Profile (read-only) work. Notification toggles are localStorage-only. "Sign out everywhere" is a no-op and "Delete account" is disabled.

## F46 — Health badge ✅
- **What:** Shows whether the backend is reachable.
- **Where:** `components/HealthBadge.tsx`, `GET /health`.

## F47 — Email notifications 🔵
- **What:** Would notify users of new important messages.
- **Status:** **Not implemented.** Notification preferences are stored but nothing sends notifications (Brevo is only used for password reset).

## F48–F52 — Planned / non-existent 🔵
- **Sign in with Google:** does not exist (Google OAuth is only for Gmail connect).
- **AI-drafted replies sent to others:** only a draft is shown; there is no send path.
- **Delete account / sign out everywhere:** presentational no-ops.
- **LinkedIn:** shown as "coming soon" only.
- **Sentiment/intent analysis:** not a separate feature; intent exists only inside the assistant.
