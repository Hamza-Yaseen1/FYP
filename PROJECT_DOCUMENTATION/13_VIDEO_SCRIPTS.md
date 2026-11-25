# 13 — Video Scripts

> Ready-to-record scripts. Four videos: a 60-second pitch, a 3-minute demo, a 5–8-minute full walkthrough, and a Google OAuth verification video. Speak naturally — these are scaffolds, not a teleprompter.

---

## Before you record (all videos)

- Have a clean account with a few realistic messages (mix of urgent, normal, and a newsletter).
- Connect a Gmail account with a handful of emails (for the OAuth video, use a **test** account with non-sensitive mail).
- Know your demo order and rehearse once.
- Close unrelated tabs/notifications; zoom the browser to ~110% so text is readable.
- State clearly that it is a **Final Year Project** by **Hamza Yaseen, BBSUL**.

---

## VIDEO 1 — The 60-second pitch

**Goal:** explain the problem, the solution, and the value in one minute.

**[0:00–0:10] — Hook**
> "Every day, important messages get buried under newsletters, spam, and chatter. I built Sift to fix that."

**[0:10–0:25] — What it is**
> "Sift connects to your Gmail and WhatsApp, and uses AI to read every message for you. It sorts them by priority, writes a short summary, and pulls out the tasks and deadlines hidden inside."

**[0:25–0:40] — Show the core screens**
> *(Dashboard → Inbox → Attention → Tasks.)*
> "This is the dashboard. The inbox lets you filter and search. The Attention view shows only what actually needs you. And every extracted task lands in a real task list you can complete or snooze."

**[0:40–0:52] — The assistant**
> *(Open the assistant, type or say: "what needs my attention?")*
> "There's also an assistant. You can ask it questions by voice or text — like what needs your attention — and it answers from your real data."

**[0:52–1:00] — Close**
> "Sift: one place for every message, already sorted. Built by Hamza Yaseen as a Final Year Project."

---

## VIDEO 2 — The 3-minute demo

**Goal:** show the end-to-end flow on real screens.

**[0:00–0:20] — Intro & problem**
> "Hi, I'm Hamza Yaseen. This is Sift — an AI system for managing communication overload. The problem: too many messages, important ones buried, deadlines hidden in long emails."

**[0:20–0:45] — Sign up / login**
> *(Register or log in.)*
> "Accounts use email and password with secure, hashed passwords and a signed session cookie."

**[0:45–1:20] — Add a message & watch the AI**
> *(Use the simulate form or show an incoming Gmail/WhatsApp message.)*
> "When a message arrives, it's deduplicated, linked to any related thread, and analysed by AI. It gets a priority, a summary, a recommended action, and any tasks or deadlines. You can see the AI's confidence, and you can correct the priority if you disagree."

**[1:20–1:50] — Inbox + filters + attention**
> *(Show tabs, filters, search.)*
> "The inbox supports tabs, filters by source, priority, sender and date, and full-text search. The Attention view uses deterministic rules — a task with a near-term deadline, or an urgent message with a task — so it's predictable and explainable."

**[1:50–2:20] — Tasks**
> *(Show tasks; complete and snooze one.)*
> "Tasks extracted from messages become a real list. I can complete them or snooze them for an hour, a day, or a week."

**[2:20–2:45] — Assistant + voice**
> *(Ask by voice: "show me yesterday's messages" then "what are my pending tasks?")*
> "The assistant works by voice or text. It can navigate, answer questions about your real messages, and perform actions — and anything destructive needs an explicit confirmation."

**[2:45–3:00] — Close**
> "Everything is private and user-scoped: you only ever see your own data. This is Sift. Thank you."

---

## VIDEO 3 — Full walkthrough (5–8 minutes)

**Goal:** a complete tour, including architecture and the honest limitations. Use this for a supervisor or examiner who wants depth.

### Section A — Introduction (0:00–0:40)
> Problem statement, who it's for, one-sentence solution. Mention the stack: Next.js frontend, FastAPI backend, MongoDB, Groq for AI.

### Section B — Architecture (0:40–1:40)
> Show the diagram from `02_SYSTEM_ARCHITECTURE.md` (or draw it).
> "The browser never calls the backend directly — Next.js rewrites API calls and keeps the session cookie on one origin. FastAPI owns all logic and is the only layer that talks to the database and the AI. Gmail and WhatsApp both feed one shared ingest pipeline."

### Section C — Authentication & security (1:40–2:40)
> Register/login; explain bcrypt, the JWT cookie, purpose-scoped reset/WS tokens, and the fact that cross-user requests return 404.

### Section D — Message ingestion & AI (2:40–4:00)
> Trigger a message. Explain dedupe, deterministic thread-linking, and then the AI pipeline: rule-based routing → one structured LLM call → explainable routing record. Be honest: **"It's not multi-agent — it's one call selected by rules, with deterministic fallbacks."**

### Section E — Attention, tasks, analytics (4:00–5:20)
> Attention rules; task list; analytics day/week/month (note: only three periods).

### Section F — Assistant (5:20–6:40)
> Demo text and voice; navigation, real-data answers, message questions, a confirmed action, and barge-in. Explain that the LLM is used sparingly and history is text-only.

### Section G — Reliability & honesty (6:40–7:30)
> "If the AI fails, messages are marked pending and retried — the app never silently shows a wrong answer. If the AI is down, the assistant falls back to deterministic replies."

### Section H — Limitations & future work (7:30–8:00)
> Be upfront: Google restricted-scope verification pending; no rate limiting on login; in-memory context; in-process background loops; account deletion is manual. Frame these as clear next steps.

---

## VIDEO 4 — Google OAuth verification video

> Google reviewers expect a clear, factual video showing the consent screen, the scope, and how the data is used. **Do not** use a personal account with sensitive mail — use a dedicated test account.

**[0:00–0:20] — Identity**
> "My name is Hamza Yaseen. This is Sift, a Final Year Project. The app connects to Gmail using the `gmail.readonly` scope only, to read and triage the user's own messages."

**[0:20–0:50] — Where the connection starts**
> *(Show the Connections page.)* "From the Connections page, the user clicks Connect Gmail."
> *(Click it.)* "This redirects to Google's official consent screen."

**[0:50–1:30] — Consent screen**
> *(Show the Google consent screen.)*
> "You can see the app name, and the single permission requested: **Read your email messages and settings** — that is `gmail.readonly`. We do not request send, delete, or any other Google scope."

**[1:30–2:10] — Grant & return**
> *(Grant.)* "After granting, Google redirects back to our callback, which securely stores the tokens (encrypted) and begins reading the inbox."
> *(Show the Connections page now showing Connected, with the email address.)*

**[2:10–3:00] — How the data is used**
> *(Show the Inbox with Gmail messages, the Attention view, and a task.)*
> "The app reads the user's messages only to display them, classify their priority, summarise them, and extract tasks and deadlines. Message content is sent to our AI provider solely for this analysis, as described in our privacy policy."

**[3:00–3:30] — Data handling & disconnect**
> "Tokens are encrypted at rest. Users can disconnect at any time from this page, which revokes access at Google and stops all reading."
> *(Disconnect, or show the button.)*

**[3:30–4:00] — Privacy policy & close**
> *(Open `/privacy`.)* "Our privacy policy explains exactly what we collect, how it's used, who processes it, and the user's rights. This is Sift, by Hamza Yaseen."

**Reviewer tips:**
- Show the **exact** scope text on the consent screen.
- Show the app **name and logo** clearly.
- Explain the **only** use of the data (read + triage).
- Show the **privacy policy URL** on screen.
- Keep it under ~4 minutes and don't cut the consent screen.

---

## Recording checklist

- [ ] Rehearsed once end-to-end.
- [ ] Demo account has realistic data.
- [ ] Gmail test account used for the OAuth video (no sensitive mail).
- [ ] Screen zoomed for readability.
- [ ] Notifications off.
- [ ] Named yourself, the project, and the institution.
- [ ] Limitations stated honestly (do not overclaim "multi-agent" or "autonomous").
