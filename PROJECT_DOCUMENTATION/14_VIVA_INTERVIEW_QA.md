# 14 — Viva / Interview Q&A

> 70 questions with strong, honest answers, grouped by theme. Where the honest answer is "not implemented" or "partial", say so — examiners reward candour and penalise overclaiming.

---

## A. Project basics

**1. What is your project in one sentence?**
Sift is a web app that ingests messages from Gmail and WhatsApp, uses AI to prioritise, summarise, and extract tasks and deadlines from each message, and presents everything in a single dashboard with a voice/text assistant.

**2. What problem does it solve?**
Communication overload: important messages get buried and deadlines hide inside long text. Sift does the first read and surfaces only what needs a human.

**3. Who is it for?**
A busy individual who lives in email and chat and wants one triage surface. It is single-user per account — there is no team/organisation concept.

**4. What is the tech stack?**
Frontend: Next.js 16 (App Router, React 19, TypeScript, Tailwind v4). Backend: Python 3.13, FastAPI, Motor (async MongoDB). Database: MongoDB Atlas. AI: Groq. Integrations: Google Gmail API, Meta WhatsApp, Brevo email. Hosting: Vercel.

**5. Why did you choose FastAPI over, say, Flask or Django?**
Async-first (needed for concurrent AI and HTTP calls), automatic OpenAPI docs, Pydantic validation, and a clean dependency-injection system for auth.

**6. Why Next.js?**
App Router with server/client components, built-in API rewrites (so the browser stays on one origin), and easy deployment on Vercel.

**7. Why MongoDB?**
Messages are semi-structured and the AI analysis is nested, so a document store fits better than rigid tables, and Atlas gives managed hosting.

**8. Is it "agentic" or "autonomous"?**
Honestly: not autonomous. It is **rule-based orchestration plus a single LLM call**. The "agents" are logical outputs, not independent actors. I describe it as "rule-routed, explainable AI" rather than multi-agent.

**9. How many users can it support?**
The architecture is multi-tenant-safe (everything is user-scoped), but the realtime and background loops are in-process, so scaling would require shared pub/sub and a worker — I'd call it "single-instance ready".

---

## B. Architecture

**10. Walk me through a request from click to data.**
Browser → `/api/...` → Next.js rewrite → FastAPI → `get_current_user` decodes the cookie → route calls a service → service queries MongoDB scoped by `user_id` → Pydantic response → browser.

**11. Why do API calls go through Next.js instead of directly to FastAPI?**
To keep the httpOnly session cookie on the same origin, avoiding cross-site cookie and CORS complications.

**12. What are the three tiers?**
Presentation (Next.js), application (FastAPI), data (MongoDB), with external services around the application tier.

**13. What runs in the background?**
Two in-process asyncio loops started in the lifespan: the Gmail poller (every 30 s) and the pending-analysis retry sweep (every 60 s). Both are skipped on the test database.

**14. Why one ingest function for all sources?**
So dedupe, thread-linking, and analysis behave identically for Gmail, WhatsApp, and manual messages — fewer edge cases.

**15. How does realtime work?**
A WebSocket per user, authenticated by cookie. The backend keeps a `user_id → sockets` map and fans out only that user's events; the frontend reconnects with backoff and falls back to polling.

---

## C. Authentication & security

**16. How are passwords stored?**
bcrypt hashes. Plaintext is never stored or logged.

**17. How are sessions maintained?**
An HS256 JWT in an httpOnly cookie (`cai_token`), 7-day expiry, `Secure`/`SameSite` in production.

**18. What stops a password-reset token being used as a session?**
`decode_token` rejects any JWT that carries a `purpose` claim; reset and WS tokens set one.

**19. How do you prevent account enumeration on password reset?**
The endpoint always returns a generic response, and a 60-second cooldown prevents flooding.

**20. How is multi-user isolation enforced?**
The owner id always comes from the session, and every query/aggregation is scoped by `user_id`. Cross-user requests return 404.

**21. Why 404 and not 403 for another user's resource?**
So an attacker can't distinguish "not yours" from "doesn't exist" — it prevents id probing.

**22. How is the WhatsApp webhook secured?**
The raw body is verified against an HMAC-SHA256 signature (`X-Hub-Signature-256`) using constant-time comparison; missing/invalid → 403.

**23. How are OAuth tokens protected?**
Encrypted with AES before storage; the refresh token is required, and disconnecting revokes at Google first.

**24. Are any secrets exposed to the browser?**
No. Only `NEXT_PUBLIC_API_BASE` (a path) and optional WS config; all keys are backend env vars.

**25. What are your biggest security gaps?**
No login rate limiting, no server-side session revocation (stateless JWT), no email verification, no explicit security headers, and Gmail restricted-scope verification is pending.

---

## D. AI pipeline

**26. Explain the AI flow.**
`process_message` → rule-based routing → trivial/no-content short-circuit (zero LLM) → one structured LLM call → gate outputs → attach an explainable routing record.

**27. Why is it not multi-agent?**
There is a single LLM call; the five "agents" are sections of one prompt/response selected by rules.

**28. What are the five agents?**
priority, summary, task_extraction, deadline_detection, recommended_action.

**29. Why route at all instead of always asking the AI for everything?**
Cost, latency, and quality — irrelevant sections invite hallucination. Routing also gives explainability.

**30. How do you keep the AI from inventing deadlines?**
The prompts explicitly forbid inventing dates, and attention/deadline logic is deterministic. Only verbatim values from provable sources are accepted for context updates.

**31. What is the routing record and why does it matter?**
A stored subdocument listing requested/run/skipped agents and whether an LLM call was made — it makes the system explainable and is strong evidence the system "reasons".

**32. How is "needs attention" decided?**
Deterministically: R1 = has a task and a near-term deadline; R2 = urgent and has a task. Not left to the LLM.

**33. What happens if the AI fails?**
The message is stored with `status="pending"` and retried every 60 s; the UI shows "Pending", never a wrong answer.

**34. What is the circuit breaker for?**
To stop hammering Groq during a daily-quota lockout (429); it cools down for a configurable period.

**35. Why disable the model's reasoning?**
The default reasoning model could burn the whole output budget on hidden reasoning and trip free-tier limits; `reasoning_effort="none"` plus a JSON format and low token cap keeps analysis reliable.

**36. How do threads get context?**
Up to 5 prior same-user messages in the same deterministic thread are rendered into a CONTEXT block; proposed updates are accepted only if verbatim from a provable source.

**37. What is token budgeting?**
A ~4-chars-per-token estimator that truncates long messages/context to fit limits while preserving the subject line; short messages pass through unchanged.

**38. Could a malicious message manipulate the AI?**
It can influence the AI's *outputs* (that's the purpose), but it cannot cause privileged actions: assistant actions are deterministic and require confirmation, and LLM intent labels are whitelisted.

---

## E. Assistant (Kestrel / JARVIS)

**39. What is the assistant's architecture?**
A layered, deterministic-first router: Phase 4 messages → Phase 2 actions → Phase 3 intents → Phase 1 routing → Phase 5 conversation.

**40. Why "deterministic first"?**
Predictability, testability, and safety. The LLM is used only where language understanding is genuinely needed.

**41. What can the assistant do?**
Navigate between screens, answer real-data questions (unread, pending tasks, attention, today's messages), answer message-content questions (counts, listings, summaries), and perform actions (create/complete/delete tasks, search, draft a reply).

**42. Why does the assistant need a confirmation?**
Destructive actions (create/delete task) return a signed, 2-minute, user-bound token; the frontend must replay with `confirmed=true`. It prevents accidental or injected destructive commands.

**43. How does voice work?**
Browser Web Speech API: `useSpeechRecognition` for input and `useSpeechSynthesis` for output. No server-side speech processing.

**44. Why chunk the text-to-speech?**
Chrome's engine truncates a single long utterance; splitting on sentence boundaries (≤280 chars) and playing chunks sequentially makes long replies fully spoken.

**45. What is barge-in and how is it implemented?**
Talking while the assistant speaks cancels the TTS, promotes the mic to Listening, and bumps a generation counter so the interrupted reply can't resurrect itself.

**46. Does the assistant ever see the database directly?**
It uses user-scoped fetchers, and conversational history injected into prompts is text-only — no DB data, no user ids, no other users.

**47. Is the assistant context persistent?**
No — it is in-memory (last 8 turns) and lost on restart; it's not shared across instances.

---

## F. Data & database

**48. What collections exist?**
`users`, `messages`, `tasks`, `connections`. The AI analysis is stored inside each message document.

**49. How do you prevent duplicate messages?**
A composite unique index `{user_id, external_message_id}`; the second insert is treated as a duplicate, and DuplicateKeyError recovery is scoped to that key.

**50. What indexes do you have?**
Unique `users.email`, sparse `reset_token_hash`, `messages{user_id, created_at}`, a text index on sender/content/summary, the composite dedupe index, task indexes on priority/created_at and snoozed_until, and a unique `connections{user_id, provider}`.

**51. How does analytics avoid cross-user leakage?**
Every pipeline starts with a `user_id` `$match`.

**52. How are tasks attributed to a time period?**
Via the parent message's `received_at` (resolved through `source_message_id`), falling back to the task's own `created_at`.

**53. Why store analysis inside the message?**
It is always read together with the message, it avoids an extra join, and it keeps the routing record co-located for explainability.

**54. What are the priority buckets?**
urgent, important, normal, low, plus `pending` for anything unknown/un-analysed — pending is kept visible, not dropped.

---

## G. Integrations

**55. How does Gmail integration work?**
Official OAuth 2.0, `gmail.readonly` only, a signed 10-minute state JWT for CSRF/identity, encrypted tokens, and a 30-second poller using an `after:` watermark.

**56. Why is the OAuth callback not auth-gated?**
Because Google calls it, not the browser with a cookie. Safety comes from the signed state binding the request to a user.

**57. Why not use the Google SDK?**
Direct REST via httpx keeps dependencies light and the flow explicit.

**58. What is the Gmail production blocker?**
`gmail.readonly` is a restricted scope; public use needs Google verification and likely a CASA security assessment, which is not done.

**59. How does WhatsApp ingestion work?**
Meta posts to the webhook; the signature is verified, the payload is parsed for text messages, and each is ingested through the shared path.

**60. What email do you send?**
Only password-reset links, via Brevo. No notifications or marketing.

---

## H. Frontend

**61. How does the frontend fetch data?**
One wrapper (`apiFetch`) with credentials, a 10-second GET cache, in-flight de-duplication, and 401 → `/login`.

**62. How do you avoid a theme flash?**
An inline script in the root layout applies the saved theme before first paint.

**63. How does the assistant persist across screens?**
It is mounted once in `DashboardLayout`, which wraps all dashboard routes.

**64. How is the UI styled?**
Tailwind v4 with CSS-variable design tokens; components must use the variables (never hex) so dark mode stays correct.

**65. What is the temporary load-testing control?**
`BulkTestButton` — explicitly marked temporary; it should be removed before production.

---

## I. Testing & deployment

**66. How do you test the backend?**
pytest against a wiped test database (`communication_ai_test`), with AI and external HTTP calls faked; an autouse fixture cleans collections around each test.

**67. Why can't you await Motor under `asyncio.run` in tests?**
Motor is bound to the TestClient's event loop; a fresh loop causes "Future attached to a different loop". Use the TestClient loop or a fake collection.

**68. How do you test the frontend?**
vitest + Testing Library in jsdom, with fakes for WebSocket and the speech APIs; every test calls `afterEach(cleanup)` because vitest globals are off.

**69. How is it deployed?**
Next.js and FastAPI on Vercel, MongoDB Atlas for data, with `BACKEND_URL` wiring the rewrite and all secrets in backend env vars.

**70. What would you do next if you had more time?**
Complete Google verification + CASA; add login rate limiting and email verification; move background work to a worker/queue; persist assistant context in Redis; add end-to-end browser tests; add push notifications; and turn the temporary load-test UI into a proper internal tool.

---

## Quick "trap" questions and safe answers

- **"So it's multi-agent?"** → "No — one rule-routed LLM call. I can show you the routing record."
- **"Is it autonomous?"** → "No; it reacts to messages and commands, plus a retry sweep."
- **"Does the AI send emails for me?"** → "No — it can draft text, but there is no send path."
- **"Is Gmail approved for production?"** → "Not yet; restricted-scope verification is pending."
- **"Does it scale to thousands of users?"** → "The data model does; realtime/background need a shared layer first."
