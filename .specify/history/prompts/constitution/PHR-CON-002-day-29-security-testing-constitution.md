---
id: PHR-CON-002
title: Day 29 Security + Testing Constitution
stage: constitution
date: 2026-09-11
surface: cli
model: opencode/big-pickle
feature: 020-security-testing
branch: main
user: user
command: constitution
labels: [constitution, security, testing, reliability, day-29, minor-bump]
links:
  spec: TODO
  ticket: TODO
  adr: N/A
  pr: TODO
files:
  - .specify/memory/constitution.md
tests: []
---

## Prompt

Create a focused constitution for Day 29 – Security + Testing.

### Context
- Project: Communication AI (FYP)
- Main features are already built (Auth, Messages, AI, Gmail, Dashboard, Analytics)
- Now we must harden security and verify critical behaviors

### Goal of Day 29:
Perform important security checks and reliability testing.

Critical tests:
1. Authentication & User Isolation
   - Can User A access User B's messages? → NO

2. Webhook Security
   - Invalid webhook signature/request → Reject

3. AI Reliability
   - If AI is unavailable → Store message and retry later (do not lose data)

4. Duplicate Prevention
   - Same message received twice → Do not create duplicate
   - Use externalMessageId to prevent duplicates

### Principles:
- Security is mandatory
- User data isolation must never break
- System should fail safely
- Prefer clear rejection over silent acceptance of bad requests
- Data must not be lost when AI fails

### Please create a short constitution that covers:
1. Purpose of Security + Testing phase
2. Core security principles
3. Reliability principles (especially AI failure handling)
4. Duplicate prevention rules
5. Quality bar for this phase

Keep it strict, clear, and practical for a university FYP.

## Response snapshot

Updated `.specify/memory/constitution.md` from v1.17.0 to v1.18.0 (MINOR). Added a
complete Day 29 Security & Reliability Hardening section covering: purpose of the
hardening phase (the 4 critical tests), 5 core security principles (isolation as an
invariant, deny-by-default, clear rejection over silent acceptance, fail closed,
secrets server-side), 5 reliability principles for AI failure handling (store-first,
pending state + retry, never block ingestion, idempotent retries, observable
degradation), 5 duplicate prevention rules (`externalMessageId` key, dedupe before
insert, coverage of all reprocessing paths, unique index as final authority,
deterministic key for key-less messages), MUST-NOT prohibitions, and a 5-point
quality bar. Added 4 compliance checklist items. Verified templates (plan/spec/
tasks derive constitution checks generically; no command templates exist);
validated zero placeholder tokens; updated Sync Impact Report and version footer.

## Outcome

- ✅ Impact: MINOR version bump (1.17.0 → 1.18.0) — new section added
- 🧪 Tests: N/A (constitution only)
- 📁 Files: `.specify/memory/constitution.md`
- 🔁 Next prompts: spec, plan, tasks for 020-security-testing
- 🧠 Reflection: Day 29 follows the established per-day pattern (purpose →
  principles → MUST-NOT → quality bar) while extending existing security/reliability
  rules rather than redefining them; duplicate prevention re-consolidates Day 23/25/26
  idempotence rules into one explicit section.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A