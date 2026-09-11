---
id: PHR-PLAN-020
title: Day 29 Security + Testing Plan
stage: plan
date: 2026-09-11
surface: cli
model: opencode/big-pickle
feature: 020-security-testing
branch: 020-security-testing
user: user
command: /sp.plan
labels: [plan, security, testing, reliability, isolation, webhook, dedupe, retry, day-29]
links:
  spec: specs/020-security-testing/spec.md
  ticket: TODO
  adr: N/A
  pr: TODO
files:
  - specs/020-security-testing/plan.md
  - specs/020-security-testing/research.md
  - specs/020-security-testing/data-model.md
  - specs/020-security-testing/contracts/security-testing.md
  - specs/020-security-testing/quickstart.md
  - AGENTS.md
tests: []
---

## Prompt

Create a practical technical implementation plan for Day 29 – Security + Testing.

### Context
- Project: Communication AI
- Main features are already built (Auth, Messages, AI, Gmail, Dashboard, Analytics)
- Now we must harden security and verify critical behaviors

### Critical Goals:
1. User Isolation
   - User A must never access User B's data

2. Webhook Security
   - Invalid webhook requests must be rejected

3. AI Reliability
   - If AI fails → save message and allow retry later

4. Duplicate Prevention
   - Use externalMessageId to prevent duplicate messages

### Please include in the plan:
1. Goal of this phase
2. Security checks to implement or verify
3. Reliability improvements (AI failure handling)
4. Duplicate prevention approach
5. Concrete test cases to run
6. Files that may need updates
7. Implementation / verification steps in order
8. Definition of Done

Keep it practical, strict, and realistic for a university FYP.
Focus more on verification + small fixes rather than big new features.

## Response snapshot

Produced `specs/020-security-testing/plan.md` (verification-first; two small
fixes) plus Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`contracts/security-testing.md`, `quickstart.md`) deliverables. Codebase audit
confirmed isolation, webhook rejection, store-first AI handling, and app-layer
dedupe already hold — and proved two real gaps: (1) the dedupe unique index is
`external_message_id` alone and the `DuplicateKeyError` recovery in
`ingest_message` is NOT user-scoped (a cross-user key collision would return
another user's message id) → fix = composite `{user_id, external_message_id}`
index + scoped recovery lookup; (2) `pending` analyses are never retried →
fix = new `services/retry_pending.py::retry_pending_analyses()` (user-scoped
sweep through `process_message`, in-place `update_one`, wired as a rate-bounded
lifespan loop mirrored on the Gmail poller, skipped on the test DB). Decisions:
key-less (simulate) + manual `POST /messages` explicitly exempt from dedupe;
single-WABA webhook owner resolution accepted as a documented limitation; zero
new dependencies/collections/endpoints. Constitution Check: all 6 gates PASS
(I/V/VII simplicity, security, progressive enhancement; Day 18 isolation; Day 23
webhook; Day 24 orchestrator; Day 29 hardening). Implementation steps are
Red-tests-first → dedupe fix → retry sweep → full `backend/tests/` green →
frontend lint+vitest no-regression → manual checks. Definition of Done mapped
to the constitution Day 29 quality bar. Ran `update-agent-context.ps1
-AgentType opencode` — AGENTS.md Active Technologies gained the 020 lines
(manual additions preserved). No leftover placeholders; no
[NEEDS CLARIFICATION].

## Outcome

- ✅ Impact: Ready-to-execute verification plan (backend-only, ~15 new tests +
  3-location behavioral fix) with research + data model + contracts + quickstart
- 🧪 Tests: N/A (plan stage — test TDD steps defined for red phase)
- 📁 Files: `plan.md`, `research.md`, `data-model.md`,
  `contracts/security-testing.md`, `quickstart.md`, `AGENTS.md`
- 🔁 Next prompts: /sp.tick (Red) → implement fixes → Green → refactor if needed
- 🧠 Reflection: Day 29 is verify-then-fix, so the audit-first structure surfaced
  real defects (non-user-scoped dedupe recovery, missing retry) that a pure
  checklist plan would have missed; the fixes stay proportional (no new deps,
  no new services), consistent with Simplicity First.

## Evaluation notes (flywheel)

- Failure modes observed: N/A (setup-plan.ps1 ran clean this time; the earlier
  create-new-feature.ps1 Join-Path failure was already recorded in the spec PHR)
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A