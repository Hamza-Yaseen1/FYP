---
id: PHR-SPEC-020
title: Day 29 Security + Testing Specification
stage: spec
date: 2026-09-11
surface: cli
model: opencode/big-pickle
feature: 020-security-testing
branch: 020-security-testing
user: user
command: /sp.specify
labels: [spec, security, testing, reliability, isolation, webhook, dedupe, day-29]
links:
  spec: specs/020-security-testing/spec.md
  ticket: TODO
  adr: N/A
  pr: TODO
files:
  - specs/020-security-testing/spec.md
  - specs/020-security-testing/checklists/requirements.md
tests: []
---

## Prompt

Create a clear and focused specification for Day 29 – Security + Testing.

Context: Project is Communication AI (FYP). Main features are already built (Auth, Messages, AI, Gmail, Dashboard, Analytics). Now we need to verify security and reliability.

Critical requirements to test and enforce:
1. Authentication and user isolation — User A must never access User B messages, tasks, or connections; all APIs must filter by authenticated user ID.
2. Webhook security — invalid or unsigned webhook requests must be rejected; only valid requests should be processed.
3. AI reliability — if the AI service is unavailable or fails: the message must still be saved, analysis can be retried later, and the system must not crash or lose the message.
4. Duplicate prevention — the same message received twice must not create duplicates; use externalMessageId to detect and prevent duplicates.

Please include in the specification:
1. Feature Overview
2. Security rules
3. Reliability rules
4. Test cases (with expected results)
5. Acceptance Criteria
6. Edge cases

Keep it strict, practical, and suitable for a university FYP.

Also note: This is a high-level specification for non-technical stakeholders. It should have:
- Core user stories for each critical requirement
- Independent test for each user story
- Clear acceptance criteria (Given/When/Then)
- Functional requirements with IDs (FR-001, FR-002, etc.)
- Measurable success criteria also with IDs (SC-001, SC-002, etc.)
- Assume what was not explicitly provided (Session-based auth is already in place today)
- No implementation details (no languages, frameworks, API details)

## Response snapshot

Created `specs/020-security-testing/spec.md` (Draft, 2026-09-11) by scaffolding via
`.specify/scripts/powershell/create-new-feature.ps1` (created and checked out branch
`020-security-testing`, copied `spec-template.md`; script aborted on a PS 5.1
`Join-Path` 3-arg incompatibility after scaffolding, so the PHR directory was created
manually at `.specify/history/prompts/020-security-testing/`). Spec structure:
Feature Overview (hardening phase, no new user features) → 4 prioritized,
independently-testable user stories (P1 isolation, P1 webhook security, P2 AI
reliability, P2 duplicate prevention) with Given/When/Then acceptance scenarios →
Edge Cases (7) → Security Rules (7) → Reliability Rules (5) → Test Cases &
Expected Results (15-row matrix TC-01..TC-15, one row per acceptance scenario/dedup
edge) → Requirements (FR-001..FR-014 + Key Entities) → Success Criteria (SC-001..SC-006)
→ Assumptions. Created `checklists/requirements.md` (Specification Quality Checklist,
all items pass) and validated the spec: zero leftover template placeholders, zero
`[NEEDS CLARIFICATION]` markers (no clarifications required — existing system +
constitution v1.18.0 provide all defaults). No coding performed at this stage.

## Outcome

- ✅ Impact: Feature branch `020-security-testing` + ready-to-plan spec (FR-001..014,
  SC-001..006, TC-01..15)
- 🧪 Tests: N/A (spec stage)
- 📁 Files: `specs/020-security-testing/spec.md`,
  `specs/020-security-testing/checklists/requirements.md`
- 🔁 Next prompts: spark → /sp.plan (Day 29) → /sp.clarify only if needed → /sp.tick,
  then implementation branch
- 🧠 Reflection: Day 29 is a verification/enforcement phase, so the spec deliberately
  reuses the existing system's defaults (session auth, sender-issued webhook secret,
  background retry) as assumptions rather than requesting clarifications; dedupe is
  specified as 'aware-of-before-insert + storage-backed' because application-only
  checks fail under simultaneous deliveries (constitution: 'unique index as final
  authority').

## Evaluation notes (flywheel)

- Failure modes observed: `create-new-feature.ps1` crashes on Windows PowerShell 5.1
  at `Join-Path $repoRoot 'history' 'prompts' $branchName` (3-arg calls unsupported);
  `rg` not installed on this host (validation used the grep tool instead).
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A