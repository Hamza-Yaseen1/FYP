---
id: phr-us2to5-polish-day25-agent-memory
title: "Day 25 Agent Memory — US2-US5 + Polish (T016-T032)"
stage: green
date: 2026-08-31
surface: cli
model: big-pickle
feature: 016-agent-memory
branch: 016-agent-memory
user: user
command: continue (after "yes" to US1 STOP ping)
labels: [memory, context, ai, day-25, us2, us3, us4, us5, polish]
links:
  spec: specs/016-agent-memory/spec.md
  plan: specs/016-agent-memory/plan.md
  tasks: specs/016-agent-memory/tasks.md
  contract: specs/016-agent-memory/contracts/ai-context-prompt-contract.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - backend/tests/test_threads.py (US2 EC-13 latest-arrival + US5 two-user tests)
  - backend/tests/test_messages.py (standalone shape + additive identity fields)
  - backend/tests/test_webhooks.py (simulate standalone identity + day-24 analysis)
  - backend/tests/test_context_ai.py (byte-compat + validation/scoping/explainability + current-message source + linked provider failure)
  - backend/tests/test_quickstart_day25.py (new - automated quickstart pass replay)
  - backend/services/ai/context.py (current-message source in validate_context_updates; build_context_block current handle line)
  - backend/services/ai/analyzer.py (pass current_message_id to provider)
  - backend/services/ai/orchestrate.py (pass current_content into validation)
  - backend/services/ai/providers/groq.py (analyze signature current_message_id)
  - backend/services/ai/providers/openai.py (parity)
  - specs/016-agent-memory/contracts/ai-context-prompt-contract.md (current message allowed as source)
  - specs/016-agent-memory/tasks.md (T001-T032 all [x])
  - AGENTS.md (016-agent-memory manual note; script refresh for opencode)
tests:
  - python -m pytest tests/test_context_ai.py tests/test_quickstart_day25.py -q (13 passed)
  - python -m pytest tests/ -q (155 passed, 0 failures)
---

## Prompt

After US1's STOP confirmation (user "yes"), complete the remaining Day 25
work: User Story 2 (unrelated messages stay independent), User Story 3
(zero regression for standalone pipeline + Dashboard), User Story 4
(explainable/dismissible context), User Story 5 (threads only contain my
messages), and Phase 8 Polish (T030 full suite, T031 quickstart, T032
constitution re-check). Tests written FIRST per tasks.md.

## Outcome

- Added the US2/US3/US4/US5 test additions from tasks.md (T016-T021,
  T023-T025, T027-T028) plus a cross-user positive-drop + a forged-value
  hardening case and an FR-012 linked-provider-failure test. All landed
  GREEN against the existing implementation.
- T022/T029 verification: frontend has zero reads of the new fields
  (pre-existing uncommitted UI redesign is NOT Day 25 work); runners
  limited to `routes/messages.py` + `webhook_ingest.py` + `threads.py`;
  every resolve/fetch/update is `user_id`-scoped.
- **Contract gap (documented decision):** the plan/spec/quickstart two-message
  flow ("Can you send the report?" → "Need it before our meeting.") enriches
  the first message naming the SECOND as the source — but the strict contract
  (source must be an earlier context-block message) made that impossible, and
  the quickstart e2e test went RED (`KeyError: 'context_updates'`). Fix,
  spec-faithful: the current message is a provable source. `build_context_block`
  now emits `[<handle>] (THIS message being analyzed ...)`; `validate_context_updates`
  accepts the current-handle source with a verbatim check against
  `current_content`; `ai-context-prompt-contract.md` amended (§1/§2/§3). 
  Frontend/prod call sites unchanged (analyzer resolves from `message_id`).
- T031 automated as `tests/test_quickstart_day25.py` (scripted 2-message flow
  on a fake collection with `_SmartFakeProvider` emitting the current-message
  source) — 13 tests in the context+quickstart run.
- T032 constitution re-check: labeled-30-pair ≤5% false / ≥80% recall
  (mock print: 0%/100%); single-call provider-count green; user isolation
  suites green; `rg -i "vector|embedding|rag"` → only doc-string/false-positive
  hits (`storage`, `pragma`), zero runtime imports; greppable `messageId`
  present at both entry points (webhook_ingest.py:83, routes/messages.py:46);
  explainability invariants enforced; AGENTS.md refreshed via
  `update-agent-context.ps1 -AgentType opencode`.
- Full backend suite: **155 passed**, 0 failures (~2m30s). T016-T032 marked
  `[x]` in tasks.md (T001-T032 all complete).

## Lessons / Notes

- First quickstart run hit `KeyError: 'context_updates'` from a fake emitting a
  full ObjectId as `source_message_id` (handle mismatch); the deeper root cause
  was the contract gap above, not the fake.
- The 2-message e2e needs the current-handle source; the byte-compat and
  single-call guarantees still hold — the handle line appears ONLY when
  `current_message_id` is provided (i.e. only with a thread).
- `pytest -k` runs are fast; the full 155-test suite needs the 300s timeout.

## Stop Condition

All Day 25 tasks complete (T001-T032 `[x]`); suite green; no further work
scheduled on this branch.