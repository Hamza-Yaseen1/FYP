---
id: phr-constitution-day26-gmail-integration
title: "Day 26 Gmail Integration Constitution"
stage: constitution
date: 2026-09-10
surface: cli
model: big-pickle
feature: gmail-integration
branch: main
user: user
command: /sp.constitution
labels: [constitution, gmail, oauth, email, day-26]
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

Create a focused constitution for Day 26 – Gmail Integration.

### Context
- Project: Communication AI (FYP)
- WhatsApp (simulated + real webhook architecture) is already prepared
- Authentication and User Isolation are working
- Now we want to connect Gmail using official Google OAuth

### Goal of Day 26:
Implement Gmail connection using Google's official OAuth flow.

Flow:
Connect Gmail
     ↓
Google OAuth
     ↓
Permission
     ↓
Gmail API
     ↓
New Email
     ↓
Our Backend (normalized message format)

### Important Rules:
- Never ask users for their Gmail password
- Only use official Google OAuth 2.0
- Store tokens securely (never expose to frontend)
- Every Gmail connection must belong to a userId
- Convert Gmail emails into the same normalized message format used by WhatsApp

### Please create a short constitution that covers:
1. Purpose of Gmail Integration
2. Security principles (OAuth only, no passwords)
3. Token handling rules
4. Normalized message principle
5. What should and should not be done
6. Quality bar for this feature

Keep it practical, secure, and suitable for a university FYP.

## Response snapshot

Updated `.specify/memory/constitution.md` from v1.13.0 to v1.14.0 (MINOR bump).

Changes made:
1. Added "Day 26 Gmail Integration" section after the Day 25 Agent Memory /
   Context, containing: Purpose (Gmail connection via OAuth flow), OAuth-Only
   Security Principle (5 rules: no passwords, Google OAuth 2.0 only, official
   API client, minimal scopes, explicit consent), Token Handling Rules (7 rules:
   encrypted at rest, never exposed to frontend, backend-only operations,
   environment-based keys, refresh lifecycle, audit trail, revocation on
   disconnect), Normalized Email Format (canonical JSON contract with 8 rules
   including source enum, human-readable sender, content extraction, server
   timestamp, externalMessageId for idempotence, nullable subject, server-side
   userId, no attachments in Day 26), Connection Ownership (6 isolation rules
   extending Day 19), Email Ingestion Flow (7-step text diagram), What the
   System MUST NOT Do (12 prohibitions), Quality Bar (13 verification criteria).
2. Added 12 new Compliance Checklist items for Gmail integration.
3. Updated Sync Impact Report at top of file.
4. Updated version footer to 1.14.0 with date 2026-09-10.

## Outcome

- ✅ Impact: Constitution updated with a focused Day 26 Gmail Integration
  section that enforces OAuth-only authentication (no passwords), encrypts
  tokens at rest, normalizes Gmail emails into the same canonical format as
  WhatsApp, maintains per-user isolation, and provides a complete quality bar
  for the Gmail connection lifecycle. The section extends existing principles
  (IV, V, VII) and the Day 19 Connection Architecture without redefining them.
- 🧪 Tests: N/A — constitution amendment only; no code tests run.
- 📁 Files: .specify/memory/constitution.md (single file modified)
- 🔁 Next prompts: /sp.spec (or /sp.plan) for the Day 26 Gmail Integration
  feature specification
- 🧠 Reflection: The MINOR bump is correct — a materially new section with no
  redefinition of existing principles. Care was taken to reconcile Gmail
  integration with existing rules: OAuth tokens follow the same encryption
  rules as WhatsApp tokens (Day 19), normalized email format mirrors the
  WhatsApp canonical format (Day 23), and user isolation is explicitly
  preserved so Gmail data never crosses user boundaries (Day 18). The
  "receive-only" scope and "no attachments" rule keep the feature practical
  for an FYP while the "revoke on disconnect" rule ensures clean security
  hygiene.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS — no remaining bracket tokens,
  version line matches report (1.13.0 → 1.14.0), dates ISO format, principles
  declarative and testable (MUST/NEVER throughout), templates require no
  updates
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
