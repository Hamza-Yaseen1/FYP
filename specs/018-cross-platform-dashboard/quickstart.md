# Quickstart: Cross-Platform Dashboard

**Phase 1 output** — how to run and verify the feature locally.

## Prerequisites

- Backend running: `python` + uvicorn from `backend/` (see repo `README`
  / existing `.env` with `MONGO_URI`).
- Frontend running: `npm run dev` from the repo root (Next.js, port 3000).
- Logged-in session (register/login) — cookie-based auth.

## Run

1. `npm run dev` (frontend) and the FastAPI backend (uvicorn) in two
   terminals.
2. Open `http://localhost:3000/dashboard`.

## Verify (mapped to Definition of Done)

1. **Unified view** — Simulate a WhatsApp message (the "Simulate a
   message" card on the dashboard) and send a Gmail test email (via the
   Gmail connection / poll). Both appear on the same Dashboard, no
   per-channel pages.
2. **Grouping** — create messages that analyze to urgent / important /
   normal / low. Confirm groups render URGENT → IMPORTANT → NORMAL → LOW
   (→ Pending), and empty groups are hidden.
3. **Card fields** — each card shows priority badge, title (task →
   summary → preview), `WhatsApp • Ali` / `Gmail • Teacher` label, and
   relative time. Deadline / subject / recommended action appear only when
   stored.
4. **Attention** — a flagged message shows its "Needs Your Attention"
   badge + "Why it matters" above the groups.
5. **Pending** — a message with `priority: "pending"` lands in the Pending
   tail with an indicator; layout intact.
6. **Isolation** — log in as a second user: dashboard shows only that
   user's messages.
7. **Regression** — Inbox, Tasks, Attention pages still work; pytest suite
   still passes.

## Stop

- No backend changes were made; nothing else needs restarting beyond
  normal dev.

## Troubleshooting

- Dashboard empty but messages exist → check you're logged in (401 would
  redirect to `/login`).
- A card shows a raw ISO timestamp → the current `useTimeAgo` formatting is
  not applied (should not happen); verify component uses `useTimeAgo`.
- Simulated message not analyzing → check the Groq/OpenAI provider env
  vars; it still appears in Pending (Progressive Enhancement).