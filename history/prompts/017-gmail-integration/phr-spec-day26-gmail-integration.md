---
id: phr-spec-day26-gmail-integration
title: "Day 26 Gmail Integration Spec"
stage: spec
date: 2026-09-10
surface: cli
model: big-pickle
feature: 017-gmail-integration
branch: 017-gmail-integration
user: user
command: /sp.spec
labels: [spec, gmail, oauth, email, day-26]
links:
  spec: specs/017-gmail-integration/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/017-gmail-integration/spec.md
  - specs/017-gmail-integration/checklists/requirements.md
tests:
  - N/A (specification phase; no code changes)
---

## Prompt

Create a clear and focused specification for Day 26 – Gmail Integration.

### Context
- Project: Communication AI
- Authentication, User Isolation, and normalized message format already exist
- WhatsApp flow is prepared
- Now we need to connect Gmail using official Google OAuth

### Goal:
Allow users to connect their Gmail account so new emails can be received
and processed by the AI system.

Flow:
Connect Gmail → Google OAuth → Permission → Gmail API → New Email → Backend
→ AI Pipeline → Dashboard

### Key Requirements:
- Use Google OAuth 2.0 only (never ask for password)
- Store accessToken and refreshToken securely
- Every connection must belong to a userId
- Convert Gmail emails into the same normalized format used for WhatsApp:
  {
    "userId": "...",
    "source": "gmail",
    "sender": "teacher@example.com",
    "content": "Please submit the report.",
    "receivedAt": "...",
    "externalMessageId": "..."
  }
- Show connection status on the Connections page
- Only the logged-in user can see/manage their own Gmail connection

### Please include in the specification:
1. Feature Overview
2. User Stories
3. OAuth flow steps
4. Data model for Gmail connection
5. Normalized email format
6. Security rules
7. Acceptance Criteria
8. Edge cases
9. What is out of scope for this day (if any)

Keep it practical, secure, and suitable for a university FYP.

## Response snapshot

Created feature branch `017-gmail-integration` and wrote the Day 26 spec.

1. Branch/dir setup: ran `create-new-feature.ps1 -Number 17 -ShortName
   "gmail-integration"` — highest existing feature number found: 016
   (agent-memory). Script hit the known PowerShell 5.1 incompatibility
   (`Join-Path` with 3 positional args) after creating the branch/spec;
   completed the missing `history/prompts/017-gmail-integration/` dir manually.
2. Wrote `specs/017-gmail-integration/spec.md` with: Feature Overview
   (second real channel, receive-only, parity with WhatsApp), 3 prioritized
   User Stories (P1 Connect via OAuth, P2 Receive new emails as normalized
   messages, P3 Manage status/disconnect), 12 Edge Cases, OAuth Flow Steps
   (7-step diagram), Normalized Email Format (canonical JSON + 7 rules),
   Security Rules (8 rules incl. OAuth-only/no-passwords, least-privilege
   scope, encrypt-at-rest, backend-only, explicit consent, server-side
   ownership, clean revocation, receive-only), Functional Requirements
   FR-001..FR-012, Key Entities (Gmail Connection, Message), Measurable
   Success Criteria SC-001..SC-008, Assumptions, and Out of Scope.
3. Ran the specification quality validation: no [NEEDS CLARIFICATION]
   markers (scope=read-only, new-emails-only, one connection per user all
   have reasonable defaults documented as Assumptions); all 12 checklist
   items pass. Wrote
   `specs/017-gmail-integration/checklists/requirements.md` with all items
   marked complete.

## Outcome

- ✅ Impact: Feature branch `017-gmail-integration` with a complete, practical
  spec for Day 26 Gmail integration. OAuth-only (no passwords), encrypted
  token storage, per-user ownership, and normalization to the same canonical
  message format as WhatsApp keep the feature consistent with the Day 26
  constitution section (v1.14.0).
- 🧪 Tests: N/A — specification phase; no code tests run.
- 📁 Files: specs/017-gmail-integration/spec.md, specs/017-gmail-integration/checklists/requirements.md
- 🔁 Next prompts: /sp.clarify (not needed — no markers) or /sp.plan for the
  Day 26 Gmail integration feature
- 🧠 Reflection: The spec mirrors the Day 25 agent-memory spec structure,
  keeping the repo's spec style consistent, and inherits technical defaults
  from the Day 26 constitution section (OAuth-only principle, token handling
  rules, normalized email format, isolation). No clarifications were required
  because the feature description supplied concrete constraints. Same
  tooling defect noted as prior features: create-new-feature.ps1 fails
  mid-way on PowerShell 5.1 due to `Join-Path` argument binding.

## Evaluation notes (flywheel)

- Failure modes observed: create-new-feature.ps1 fails with "positional
  parameter cannot accept argument 'prompts'" on Windows PowerShell 5.1
  (Join-Path accepts only 2 positional params there; script targets pwsh 7).
  Branch, feature dir, and spec template were created before the failure, so
  manual completion of the prompts dir resolved it.
- Graders run and results (PASS/FAIL): PASS — no placeholder tokens, mandatory
  template sections preserved, FRs/SCs testable and technology-agnostic, edge
  cases covered, security rules traceable to the Day 26 constitution,
  checklist complete
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A