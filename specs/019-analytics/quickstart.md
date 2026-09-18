# Quickstart — Analytics (Day 28)

**Purpose**: Hands-on validation that the Analytics feature works end-to-end.
Run after the two-user checks behind auth, plus the new endpoint.

## 1. Prerequisites

- Backend running: `cd backend && uvicorn main:app --reload` (port 8000)
- Frontend running: `npm run dev` (port 3000)
- Mongo reachable (`.env` → `MONGO_URI`)

## 2. Endpoint smoke test

```bash
# No cookie → 401
curl -i http://localhost:8000/analytics | findstr /i "401"

# Invalid period → 400
curl -i -b SESSION_COOKIE http://localhost:8000/analytics?period=year

# Valid call (after logging in via UI or register/login API)
curl -b SESSION_COOKIE "http://localhost:8000/analytics?period=week"
```

## 3. Data seeding (via existing simulate webhook)

While logged in, from the frontend Dashboard use the simulate box to send
several messages with clear priorities:
- At least one urgent ("Submit the form right now"), one important
  ("Review this by tomorrow"), one normal, one routine/low.
- Some WhatsApp-source, some Gmail-source.
- Mix `received_at` across today / this week / earlier than 7 days (only via
  direct DB insert or with waited timestamps) to exercise the period toggle.

## 4. UI validation

1. Open `/analytics` → sidebar shows an "Analytics" link; page title
   "Communication Overview — This Week".
2. Summary cards match the simulate counts exactly (Total, Urgent, Important,
   Normal, Low).
3. Source chart shows WhatsApp + Gmail bars with the counts above.
4. Priority distribution chart segments match the cards.
5. "Tasks Completed" reflects completed vs total after completing a task on
   `/tasks`.
6. Toggle Today / This Week / This Month → cards + all charts update without a
   page reload; default period is This Week.
7. Switch theme (light ⇄ dark) → charts and text remain legible.

## 5. Empty & edge states

- Log in as a brand-new user → "No data yet" empty state, no broken charts.
- Zero messages today but some this week → Today shows the empty state for each
  section.
- Only WhatsApp connected → source chart shows a single bar, no empty Gmail bar.
- Delete/complete all tasks → Tasks shows "No tasks extracted yet" (or 0 of N
  state).

## 6. Isolation check

Register users A and B. Give A 10 messages. Log out, log in as B → `/analytics`
shows B's numbers (0), never A's. Swap back → A still sees 10.

## 7. Passing criteria

- All counts match direct DB counts for the same period/filters.
- Two-user isolation holds via UI and direct API (guessed IDs included).
- Page loads < 2s with 10,000 messages; toggle < 1s.
- Light/dark + desktop/tablet readable.
- No regression: Dashboard, Inbox, Tasks, Connections still work.