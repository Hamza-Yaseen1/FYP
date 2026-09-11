---
id: PHR-TASKS-020
title: Day 29 Security + Testing Tasks
stage: tasks
date: 2026-09-11
surface: cli
model: opencode/big-pickle
feature: 020-security-testing
branch: 020-security-testing
user: user
command: /sp.tasks
labels: [tasks, security, testing, reliability, isolation, webhook, dedupe, retry, day-29]
links:
  spec: specs/020-security-testing/spec.md
  plan: specs/020-security-testing/plan.md
  research: specs/020-security-testing/research.md
  data-model: specs/020-security-testing/data-model.md
  contracts: specs/020-security-testing/contracts/security-testing.md
  quickstart: specs/020-security-testing/quickstart.md
  ticket: TODO
  pr: TODO
files:
  - specs/020-security-testing/tasks.md
tests: []
---

## Prompt

Generate the task list for Day 29 – Security + Testing.

### Critical Input
- feature 020-security-testing
- goal: Security hardening — verify existing isolation + webhook security, fix dedupe scope, add retry sweep

### Work Already Done
- spec: 4 user stories (US1-P1 isolation, US2-P1 webhook, US3-P2 AI reliability, US4-P2 dedupe)
- plan: verification-first; 2 surgical fixes; TDD red-first approach
- research: isolation verified, webhook verified, retry gap found, dedupe gap found, zero new deps
- data-model: user-scoped dedupe key, pending → retry → completed lifecycle
- contracts: retry_pending_analyses() contract, verification surface for all endpoints

### Critical Goals
1. Tests written first (TDD red-green)
2. US1 + US2 verification-only (no code changes)
3. US3: new retry_pending.py + lifespan wiring
4. US4: composite index + scoped recovery in webhook_ingest.py
5. Full suite green, zero frontend changes

### Tests Required
Yes — user explicitly requested concrete test cases + TDD approach in plan.

### Please include in the task list:
- Tests per user story (organized by story)
- Code fix tasks (only US3 and US4)
- Exact file paths
- Parallel markers [P] where applicable
- Execution order and dependencies

## Response snapshot

Produced `specs/020-security-testing/tasks.md` — 34 tasks across 7 phases:

- Phase 1 Setup (T001-T002): confirm existing 212-test baseline green, verify test env
- Phase 2 Foundational (T003): confirm existing isolation tests pass (baseline for US1)
- Phase 3 US1 Isolation (T004-T008): 5 tests extending A/B matrix to connections +
  analytics with guessed-ObjectId probes and 404-body-equality assertions — all
  PASS against existing code, no code changes
- Phase 4 US2 Webhook (T009-T012): 3 tests backfilling malformed JSON, non-SHA256
  header, and valid-sig-wrong-secret negatives — all PASS against existing code,
  no code changes
- Phase 5 US3 AI Reliability (T013-T021): 5 tests (T013-T015 PASS today, T016-T017
  RED until fix) + retry_pending.py creation (T019) + lifespan wiring (T020)
- Phase 6 US4 Duplicate Prevention (T022-T029): 4 tests (T022-T023/T025 PASS today,
  T024 RED until fix) + composite index in main.py (T027) + user-scoped recovery
  in webhook_ingest.py (T028)
- Phase 7 Polish (T030-T034): full backend suite, frontend no-regression, AGENTS.md,
  manual smoke

US1+US2 parallel, US3+US4 parallel (different file regions). TDD discipline enforced
within each story.

## Outcome

- ✅ Impact: Ready-to-execute task list — 34 tasks, 7 phases, TDD red-first within each story
- 🧪 Tests: 15 new tests across 4 files (test_security_testing, test_webhooks backfill,
  test_ai_reliability, test_dedup)
- 📁 Files: `tasks.md`
- 🔁 Next: Execute T001 → proceed through phases → commit after each code-fix task
- 🧠 Reflection: Organizing by user story rather than by fix phase makes each story
  independently deployable; US1/US2 are pure verification with zero code changes,
  keeping the critical P1 security invariant checks lightweight.

## Evaluation notes (flywheel)

- Failure modes observed: N/A
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
