---
id: phr-015-ai-orchestrator-plan-001
title: Day 24 AI Orchestrator Plan
stage: plan
date: 2026-08-29
surface: cli
model: big-pickle
feature: ai-orchestrator
branch: 015-ai-orchestrator
user: user
command: /sp.plan
labels: [plan, day24, ai-orchestrator, routing, gating, trivial-skip]
links:
  spec: specs/015-ai-orchestrator/spec.md
  plan: specs/015-ai-orchestrator/plan.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/015-ai-orchestrator/plan.md
  - specs/015-ai-orchestrator/research.md
  - specs/015-ai-orchestrator/data-model.md
  - specs/015-ai-orchestrator/contracts/ai-analysis-contract.md
  - specs/015-ai-orchestrator/quickstart.md
tests:
  - N/A
---

## Prompt

Create a clear and focused implementation plan for Day 24 – AI Orchestrator,
based on the specification for feature 015-ai-orchestrator.

## Response snapshot

Created plan for feature `ai-orchestrator` on branch `015-ai-orchestrator`:

- specs/015-ai-orchestrator/plan.md — Summary (selection-based orchestration,
  single-call preserved, trivial-skip, dashboard unchanged), Technical Context,
  Constitution Check (PASS all gates, incl. single-call, Priority-never-skipped,
  Day 23 + isolation), structure, Technical Approach (rule-based routing →
  gating → attention on gated state), agent decision table, 7 ordered
  implementation steps with checkpoints, testing plan (decision-table unit
  tests, mocked-provider call-count ≤ 1, gating, task-persistence gate,
  regression) and a 10-item Definition of Done mapped to SC-001..SC-008.
- specs/015-ai-orchestrator/research.md — Phase 0: problem + constraints,
  code facts, 6 decisions (routing = selection not extra calls; unified
  rule signals incl. `unicodedata` script check; deterministic trivial
  defaults; attention on gated analysis; failure(`pending`) vs
  skip distinguishable; one entry point), code inventory, risks, open
  questions.
- specs/015-ai-orchestrator/data-model.md — Phase 1: `ai_analysis.routing`
  subdocument (agents_run, agents_skipped, skip_reason, triggers,
  llm_call_used, decided_at), the `skipped` stub shape, the declaration of
  `RoutingRecord` + `AIAnalysis.routing` in models/message.py, task-collection
  gating, no new indexes.
- specs/015-ai-orchestrator/contracts/ai-analysis-contract.md — existing
  endpoints carved into a stored-analysis contract: the modeling rules table
  (condition → needs_analysis/needs_llm/outputs/tasks/status), routing
  invariants, single-call budget guarantee, no new env vars.
- specs/015-ai-orchestrator/quickstart.md — Day 24 runbook (routing-table
  checks without LLM, E2E simulate exercises for trivial/rich/FYI/media,
  dashboard contract check, pytest commands, troubleshooting).
- AGENTS.md updated via update-agent-context.ps1; truncated auto-lines
  manually corrected.

Design discovery during planning: `AIAnalysis` is a strict Pydantic model
(v2.12.5, `extra='ignore'`), so `message_doc_to_response` would silently drop
an un-declared `routing` key from API responses — the plan now includes
declaring `RoutingRecord`/`routing` on the model as a first-class step.

## Outcome

- ✅ Impact: The plan pins a single design — a pure rule-based
  `routing.py::decide_routing` + a thin `orchestrate.py::process_message`
  that (a) produces deterministic defaults for trivial/skipped messages with
  ZERO AI calls and (b) otherwise reuses the existing single-call
  `analyze_message` with output-gating and task-persistence gating. The
  Dashboard and API surface stay backward compatible.
- 🧪 Tests: N/A (planning stage) — but the Testing Plan mandates
  decision-table unit tests, provider-invocation counting (trivial=0,
  rich=exactly ≤1), gating asserts, and no task inserts when the task agent is
  skipped.
- 📁 Files: plan.md, research.md, data-model.md, contracts/ai-analysis-contract.md,
  quickstart.md (all under specs/015-ai-orchestrator/)
- 🔁 Next prompts: /sp.tasks for ai-orchestrator
- 🧠 Reflection: The Pydantic-extra-keys discovery is the most valuable single
  finding — it prevented a latent bug where routing would be stored but never
  surfaced in the API. The "routing = selection, not per-agent calls" framing
  resolves the tension between the constitution's single-call rule and a
  multi-agent appearance.

## Evaluation notes (flywheel)

- Failure modes observed: update-agent-context.ps1 emits truncated bullets
  (it copies only the first line of multi-line dependency bullets) — the
  AGENTS.md `Active Technologies` entries were rewritten by hand to the full
  intended text. The known PowerShell 5.1 create-new-feature.ps1 quirk did not
  resurface (branch/spec already existed this session).
- Graders run and results (PASS/FAIL): PASS — Technical Context, Constitution
  Check, file-level plan, implementation steps, testing plan, Definition of
  Done present; no placeholders; all spec success criteria traceable to DoD.
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A