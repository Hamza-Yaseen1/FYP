---
id: phr-20260821-tasks-pipeline
title: Day 14 Pipeline Task List
stage: tasks
date: 2026-08-21
surface: cli
model: big-pickle
feature: 006-complete-ai-pipeline
branch: 006-complete-ai-pipeline
user: user
command: /sp.tasks
labels: [tasks, ai-pipeline, dashboard, day-14]
links:
  spec: specs/006-complete-ai-pipeline/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/006-complete-ai-pipeline/tasks.md
tests:
  - backend/test_attention_pipeline.py (planned by T005/T006/T013)
---

## Prompt

Create a clear and actionable task list for Day 14 – Complete AI Pipeline.

### Context
- Project: Communication AI
- Individual AI features already exist (Priority, Summary, Task Extraction, Deadline, Recommended Action)
- Now we need to connect everything into one clean pipeline and improve the Dashboard display

### Goal:
When a message arrives, the full AI pipeline runs and the Dashboard shows a clear card like:

🔴 NEEDS ATTENTION
Send FYP slides
WhatsApp • Ali
Deadline: Tonight
Why it matters: A task with a near deadline was detected.
Recommended: Send the slides before tonight.

### Focus Areas:
- Make sure the full AI pipeline runs in correct order
- Ensure all results (priority, summary, task, deadline, recommended action) are saved properly
- Improve the “Needs Attention” section on the Dashboard
- Show clear information: Task name, Source, Deadline, Why it matters, Recommended action
- Keep the UI clean and professional

### Requirements for the task list:
- Break work into small, clear, executable tasks
- Group tasks logically (Backend Pipeline, Data Structure, Frontend Display, Testing)
- Write tasks in action language
- Include acceptance criteria for important tasks
- Follow Simplicity First principle

Save the file in the appropriate location.

## Response snapshot

Generated specs/006-complete-ai-pipeline/tasks.md with 16 checklist-format tasks across 6 phases: Setup baseline verification (T001), Foundational data structure — AIAnalysis fields (T002), US1 pipeline reliability + duplicate guard + integration test (T003–T005), US2 red-green attention tests → pure evaluate_attention module → analyzer wiring → NeedsAttentionCard component → dashboard/attention page integration (T006–T012), US3 degradation tests + manual verification (T013–T014), Polish regression sweep + quickstart DoD pass (T015–T016). User's logical groups mapped onto story organization (Data Structure→Phase 2, Backend Pipeline→US1, Frontend Display→US2, Testing→US3+Polish). Acceptance criteria embedded under key tasks; dependency graph and parallel tracks defined; MVP scope = US1 only.

## Outcome

- ✅ Impact: Executable task list ready; each task self-contained with file paths
- 🧪 Tests: Test tasks included per plan (red-green for attention rules)
- 📁 Files: specs/006-complete-ai-pipeline/tasks.md
- 🔁 Next prompts: /sp.implement or begin T001; then green/refactor PHRs per story
- 🧠 Reflection: Keeping T009 (component) parallelizable against the backend track lets frontend and backend proceed independently — matches Vertical Slices principle

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Format validation PASS — all 16 tasks have checkbox+ID+path; story labels present on all Phase 3–5 tasks only
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
