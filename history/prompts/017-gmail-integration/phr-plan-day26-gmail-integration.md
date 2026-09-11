---
id: phr-plan-day26-gmail-integration
title: "Day 26 Gmail Integration Plan"
stage: plan
date: 2026-09-10
surface: cli
model: big-pickle
feature: 017-gmail-integration
branch: 017-gmail-integration
user: user
command: /sp.plan
labels: [plan, gmail, oauth, httpx, day-26]
links:
  spec: specs/017-gmail-integration/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/017-gmail-integration/plan.md
  - specs/017-gmail-integration/research.md
  - specs/017-gmail-integration/data-model.md
  - specs/017-gmail-integration/quickstart.md
  - specs/017-gmail-integration/contracts/gmail-oauth-api.md
  - AGENTS.md
tests:
  - N/A (planning phase; no code changes)
---

## Prompt

Create a plan document for Day 26 Gmail Integration. The plan must have
real data (no placeholders or [REMOVE IF UNUSED] markers), Technical Context
(Language/Version, Primary Dependencies, Storage, Testing, Target Platform,
Project Type, Performance Goals, Constraints, Scale/Scope), a Constitution
Check gate, Project Structure, Complexity Tracking, and coverage of Phase 0
(research) and Phase 1 (design: data model, contracts, quickstart) outputs.

Then update the opencode agent context from the filled plan and do a
final constitution re-check.

## Response snapshot

Created the four plan-phase outputs and updated AGENTS.md on branch
`017-gmail-integration`:

1. **plan.md** — filled the template (no placeholders). Summary, Technical
   Context (Python 3.13 + TypeScript 5.x, FastAPI/Motor/Pydantic, `httpx`
   promoted to runtime dep, MongoDB, pytest + TestClient, web monorepo,
   ≤5-min new-email performance goal, read-only/encrypted-at-rest/per-user
   constraints), Constitution Check with 12 gates — all PASS, no failures,
   no complexity violations beyond two justified entries (asyncio poller,
   direct REST vs Google SDK).
2. **research.md** — resolved every technical unknown: direct REST over
   Google endpoints (oauth2/tokeninfo/revoke/gmail API) via `httpx` instead
   of the Google SDK; `state` = short-lived HS256 JWT (PyJWT, `JWT_SECRET`)
   with `purpose: gmail_oauth` + `sub: user_id` (no state store); tokens
   encrypted with existing `utils/encryption.py` + `token_expires_at` and
   proactive refresh, `invalid_grant` → `status=error`; new-email detection
   via date-based query `after:<epoch>` tracked by `last_fetched_at`
   (read-only compatible, avoids `is:unread` endless re-scan); poller as an
   asyncio task in `main.py` lifespan (interval env, default 30s); Gmail
   emails normalized via stdlib `email` parser to canonical fields;
   `ingest_message` extended with `subject` param and self-analysis via
   `asyncio.create_task` when no `BackgroundTasks`; risk register with
   mitigations.
3. **data-model.md** — additive-only: `connections` gains `token_expires_at`,
   `last_fetched_at`, `gmail_email` (all optional); `messages` gains optional
   `subject`; `ingest_message` signature change (`subject`, spawn task);
   status transition table; no new indexes needed; API responses unchanged
   (tokens never returned); isolation guarantees restated.
4. **contracts/gmail-oauth-api.md** — `GET /connections/gmail/auth-url`
   (JWT, returns Google auth URL with signed-state), `GET
   /connections/gmail/callback` (code+state exchange → 302
   `FRONTEND_URL/connections?gmail=connected|error`), extended `DELETE
   /connections/{id}` (revoke for gmail), internal ingest + poller
   contracts, env-var table, frontend call shapes.
5. **quickstart.md** — manual Google Cloud OAuth client setup (consent
   screen External/Test, `gmail.readonly` scope, Authorized redirect URI
   `http://localhost:8000/connections/gmail/callback`), env wiring,
   connect/verify runbook, debugging table, explicit non-goals.
6. **AGENTS.md** — ran `update-agent-context.ps1 -AgentType opencode`; it
   added the two 017 Active Technologies entries but its
   `## Recent Changes` update was skipped by a pre-existing script bug (the
   Active-Technologies section swallows the next section header), so I
   appended the `- 017-gmail-integration: Added …` Recent Changes entry
   manually. The `nextjs-agent-rules` block and manual additions were
   preserved.

Constitution re-checked after design: all 12 gates still pass
(OAuth-only, minimal `gmail.readonly` scope, AES-256 encrypt-at-rest via
existing util, tokens backend-only, server-side ownership via signed state,
normalized format + additive `subject`, `external_message_id` dedup, revoke
on disconnect, receive-only polling, per-user isolation with 404/state
binding, progressive enhancement, simplicity-first).

## Outcome

- ✅ Impact: A database of implementation decisions is recorded so the
  /sp.tasks phase can produce concrete tasks. Key design locked: direct
  REST + `httpx`, signed-JWT OAuth state, date-watermarked read-only
  polling as an asyncio lifespan task, `subject`-aware ingest with
  task-spawn analysis, revoke-on-delete.
- 🧪 Tests: N/A — planning phase; no code changed or run.
- 📁 Files: plan.md, research.md, data-model.md, quickstart.md,
  contracts/gmail-oauth-api.md, AGENTS.md (Updated)
- 🔁 Next prompts: /sp.tasks to break the plan into implementation tasks,
  or /sp.adr if an architecture decision record for the direct-REST-vs-SDK
  and poller choices is wanted.
- 🧠 Reflection: The scripted agent-context update has a latent ordering
  bug worth noting for future features (it consumed the `## Recent Changes`
  header under Active-Technologies handling). Plan kept the repo's
  template-driven style while every section carries real, testable
  decisions grounded in the Day 26 constitution (v1.14.0).

## Evaluation notes (flywheel)

- Failure modes observed: (a) `update-agent-context.ps1` did not add the
  Recent Changes entry — its in-line section-state logic exits
  Active-Technologies when it sees the NEXT `## ` header, so the `##
  Recent Changes` branch never runs; workaround: hand-add entry. (b)
  PowerShell 5.1 console renders the em dash in plan storage line as `-`
  when parsing (cosmetic; does not affect extraction).
- Graders run and results (PASS/FAIL): PASS — no `[NEEDS CLARIFICATION]`
  or `[REMOVE IF UNUSED]` tokens, Technical Context fields populated,
  Constitution Check gate + re-check recorded, research decisions all
  resolved, Phase 1 docs render, scripted AGENTS.md update ran green.
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Patch `update-agent-context.ps1`
  so the Recent Changes branch runs before the Active-Technologies exit
  branch (or match the header BEFORE the in-section exit), then re-run to
  confirm AGENTS.md updates without manual edits.