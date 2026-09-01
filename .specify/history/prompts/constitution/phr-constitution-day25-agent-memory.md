---
id: phr-constitution-day25-agent-memory
title: "Day 25 Agent Memory / Context Constitution"
stage: constitution
date: 2026-08-29
surface: cli
model: big-pickle
feature: agent-memory
branch: main
user: user
command: /sp.constitution
labels: [constitution, memory, context, ai, day-25]
links:
  spec: N/A
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - .specify/memory/constitution.md
tests:
  - N/A (constitution amendment; no code changes)
---

## Prompt

Create a focused constitution for Day 25 – Agent Memory / Context.

### Context
- Project: Communication AI (FYP)
- AI Orchestrator and individual agents are already working
- Currently each message is analyzed in isolation
- Now we want the system to understand context between related messages

### Goal of Day 25:
The AI should not analyze every message alone.

Example:
Message 1: "Can you send the report?"
Message 2: "Need it before our meeting tomorrow."

The system should be able to associate these messages when appropriate.

### We should store:
- conversationId
- threadId
- messageId

### Principles:
- Keep context handling simple
- Do not over-engineer memory
- Only link messages when it clearly makes sense
- Still follow "AI is Assistive, not Magical"

### Please create a short constitution that covers:
1. Purpose of Agent Memory / Context
2. Core principles for linking messages
3. What should be stored
4. What the system should NOT do
5. Quality bar for this feature

Keep it practical and suitable for a university FYP.

## Response snapshot

Updated `.specify/memory/constitution.md` from v1.12.0 to v1.13.0 (MINOR bump).

Changes made:
1. Added "Day 25 Agent Memory / Context" section after the Day 24 AI
   Orchestrator, containing: Purpose (message-pair example), Core Principles
   for Linking Messages (6 rules incl. link-only-when-clear, context-is-
   additive, idle-by-default, assistive-not-magical, isolation, no memory
   framework), What MUST Be Stored (messageId/threadId/conversationId table +
   6 contract rules), Bounded AI-call context window (single-call, cap 5,
   user facts win, Orchestrator still decides), What the System MUST NOT Do
   (7 prohibitions), Quality Bar (7 verification criteria).
2. Added 7 new Compliance Checklist items for Day 25 context handling.
3. Updated Sync Impact Report at top of file.
4. Updated version footer to 1.13.0 with date 2026-08-29.

## Outcome

- ✅ Impact: Constitution updated with a focused Day 25 Agent Memory /
  Context section that keeps linking deterministic and rule-based, binds
  context to the existing single-LLM-call pipeline, and explicitly bans
  memory frameworks (vector store/RAG); compliance checklist expanded with
  context-handling checks.
- 🧪 Tests: N/A — constitution amendment only; no code tests run.
- 📁 Files: .specify/memory/constitution.md (single file modified)
- 🔁 Next prompts: /sp.spec (or /sp.plan) for the Day 25 Agent Memory /
  Context feature specification
- 🧠 Reflection: The MINOR bump is correct — a materially new section with no
  redefinition of existing principles. Care was taken to reconcile context
  with existing rules rather than contradict them: linking is deterministic,
  context rides inside the existing single LLM call (Complete AI Pipeline),
  and Day 18 user isolation is explicitly preserved so a thread never spans
  users. The three scoped stored fields keep the feature practical for an FYP
  while the "no memory framework" rule guards Principle I (Simplicity First).

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS — no remaining bracket tokens,
  version line matches report (1.12.0 → 1.13.0), dates ISO format, principles
  declarative and testable (MUST/NEVER throughout), templates require no
  updates
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A