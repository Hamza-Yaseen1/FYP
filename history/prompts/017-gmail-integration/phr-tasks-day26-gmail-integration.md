---
id: phr-tasks-day26-gmail-integration
title: "Day 26 Gmail Tasks"
stage: tasks
date: 2026-09-10
surface: cli
model: big-pickle
feature: 017-gmail-integration
branch: 017-gmail-integration
user: user
command: /sp.tasks
labels: [tasks, gmail, oauth, poller, day-26]
links:
  spec: specs/017-gmail-integration/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/017-gmail-integration/tasks.md
tests:
  - N/A (task list; no code changes in this step)
---

## Prompt

Create a clear and actionable task list for Day 26 – Gmail Integration.

### Context
- Project: Communication AI
- Authentication and User Isolation are working
- Connections page already exists
- Normalized message format already exists
- We must use official Google OAuth 2.0 only (never ask for password)

### Goal:
Connect Gmail → Google OAuth → Store tokens securely → Fetch/receive emails → Convert to normalized format → AI Pipeline → Dashboard

### Focus Areas:
1. Google Cloud Console manual setup (OAuth Client ID & Secret)
2. Backend OAuth endpoints (start login + callback)
3. Securely store accessToken + refreshToken linked to userId
4. Update Connections page (Connect / Disconnect / status)
5. Fetch recent emails (or simple polling for new emails)
6. Convert Gmail messages into the same normalized format used for WhatsApp
7. Trigger existing AI pipeline
8. Security (tokens never sent to frontend)

### Requirements for the task list:
- Break work into small, clear, executable tasks
- Clearly separate Manual Setup tasks vs Code tasks
- Group by: Google Setup, Backend, Frontend, Email Ingestion, Testing
- Write tasks in action language
- Include acceptance criteria for important tasks
- Keep it realistic for a university FYP (prefer simple polling over full Pub/Sub if needed)
- Follow Security & Simplicity First principles

Save the file in the appropriate location.

## Response snapshot

Ran the /sp.tasks workflow for `017-gmail-integration` and wrote
`specs/017-gmail-integration/tasks.md` (32 tasks, IDs unique, all lines in
the strict `- [ ] T### [P?] [US?] ...` checklist format — machine-validated
with Select-String).

1. Confirmed feature dir/paths: frontend lives at repo root (`app/`,
   `components/`, `lib/`); backend under `backend/` (`routes/`, `services/`,
   `models/`, `utils/`, `tests/`). Verified real files exist for every path a
   task touches via `Read` (ConnectionCard, connections page, inbox Page +
   Message interface, lib/api/connections.ts, backend routes/services/model,
   ingest_message signature) so tasks are immediately executable.
2. Grouped per the user's request with a "Grouping Map" (Google Setup /
   Backend / Frontend / Email Ingestion / Testing) on top of the
   template's user-story phases:
   - **Phase 1 Setup — Google Setup**: T001–T002 (MANUAL: consent screen w/
     gmail.readonly scope + OAuth web client + redirect URI), T003 env vars,
     T004 [P] add `httpx`.
   - **Phase 2 Foundational (blocking)**: T005 [P] connection model fields
     (token_expires_at, last_fetched_at, gmail_email), T006 [P] connection
     service upsert/refresh/error ops, T007 [P] ingest `subject` +
     asyncio-spawn analysis, T008 [P] gmail guard on POST /connections.
   - **Phase 3 US1 (P1, MVP) Connect Gmail**: tests T009–T010 first
     (test_gmail_oauth.py), then services/gmail.py OAuth helpers →
     routes/gmail.py auth-url + callback (302 connected|error) → frontend
     getGmailAuthUrl + ConnectionCard redirect + result banner.
   - **Phase 4 US2 (P2) Receive emails**: tests T017–T018 (normalize +
     poller→ingest+dedup), then normalize_email, ensure_access_token/Gmail
     client, poll_connected_gmail watermark, main.py lifespan task, subject in
     message response + Inbox card.
   - **Phase 5 US3 (P3) Manage/Disconnect**: test T025 (revoke+delete, 404
     isolation), delete_connection revoke, revoke_app + error plumbing,
     error-state Reconnect CTA.
   - **Phase 6 Polish**: no-regression suites, quickstart/2-user isolation,
     AGENTS.md note, token-leak security pass.
3. Acceptance criteria written under the important tasks (OAuth consent sane,
   redirect URI match, no refresh_token → error, tokens never user-visible,
   etc.). Polling (not Pub/Sub) chosen per research. Tests flagged to be
   written FIRST and FAIL before implementation. Dependency graph + parallel
   example + MVP-first/incremental strategy included.

## Outcome

- ✅ Impact: A ready-to-run task list (32 tasks: 4 setup incl. 2 MANUAL, 4
  foundational, 8 US1, 8 US2, 4 US3, 4 polish) grounded in real file paths
  and the plan's contracts/data-model/research. Simple asyncio poller chosen
  over Pub/Sub, matching FYP + Simplicity First.
- 🧪 Tests: N/A for this step (task generation); test tasks within the list
  are T009, T010, T017, T018, T025.
- 📁 Files: specs/017-gmail-integration/tasks.md
- 🔁 Next prompts: /sp.adr for the direct-REST + poller ADR (optional), or
  begin execution of tasks.md (T001–T004 → foundation → US1 MVP).
- 🧠 Reflection: This feature has NO new standalone tests to write in this
  phase because /sp.tasks is planning-only; the meaningful next verification
  is running the full suite after Phase 2 and clicking through OAuth after US1.

## Evaluation notes (flywheel)

- Failure modes observed: `create-phr.sh` unavailable on this Windows host —
  `/bin/bash` not present (exit 127) — so the PHR was written agent-native
  from `templates/phr-template.prompt.md` (documented fallback).
- Graders run and results (PASS/FAIL): PASS — 32/32 task lines match
  `^- \[ \] T\d{3}( \[P\])?( \[US[123]\])? `; IDs unique; every referenced
  file verified to exist; manual vs code tasks explicitly separated; Testing
  group present per request.
- Prompt variant (if applicable): /sp.tasks (standard)
- Next experiment (smallest change to try): After implementation, validate
  SC-002/SC-003 live (real email ≤5 min, zero duplicates) and run `pytest` +
  `npx vitest run` for SC-008 regression.