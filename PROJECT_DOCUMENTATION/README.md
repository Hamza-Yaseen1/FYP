# Sift — Project Documentation

> Complete, source-verified documentation of **Sift** (internally "JARVIS"), an agentic-style AI system for intelligent communication overload management.
> **Author:** Hamza Yaseen · **Institution:** BBSUL · **Type:** Final Year Project

---

## What is Sift?

A web application that connects to **Gmail** (read-only OAuth) and **WhatsApp** (webhook), uses **AI** to prioritise, summarise, and extract tasks/deadlines from each message, and presents everything in one dashboard with a voice/text assistant (**Kestrel**).

**Stack:** Next.js 16 · React 19 · TypeScript · Tailwind v4 · FastAPI · Python 3.13 · MongoDB Atlas · Groq · Vercel.

> **Honest framing:** Sift uses **rule-based routing + a single LLM call**. It is *not* a multi-agent autonomous system. See `06_AI_AND_AGENTIC_SYSTEM.md` and `15_FINDINGS_AND_GAPS.md`.

---

## Reading order

### If you are new to the project
1. `00_PROJECT_OVERVIEW.md` — what it is, who it's for, honest status.
2. `12_LEARN_MY_PROJECT.md` — guided learning path with self-test.
3. `03_ALL_FEATURES.md` — every feature with its real status.

### If you are the author preparing to present
1. `14_VIVA_INTERVIEW_QA.md` — 70 Q&A + trap questions.
2. `13_VIDEO_SCRIPTS.md` — 60s / 3min / 5–8min / OAuth video scripts.
3. `15_FINDINGS_AND_GAPS.md` — discrepancies and risks you must know.
4. `06_AI_AND_AGENTIC_SYSTEM.md` — the "is it agentic?" answer.

### If you are a developer joining
1. `02_SYSTEM_ARCHITECTURE.md` — how it fits together (diagrams).
2. `01_FILE_BY_FILE_ANALYSIS.md` — every file explained.
3. `04_FRONTEND_EXPLAINED.md` + `05_BACKEND_AND_APIS.md` — the two tiers.
4. `07_DATABASE.md` — data model.
5. `09_SECURITY_AND_PRIVACY.md` — how data is protected.

### If you are an examiner/supervisor
1. `00_PROJECT_OVERVIEW.md` — scope and honest status.
2. `06_AI_AND_AGENTIC_SYSTEM.md` — the AI design.
3. `09_SECURITY_AND_PRIVACY.md` — security posture.
4. `11_TESTING_AND_DEPLOYMENT.md` — verification and deployment.
5. `15_FINDINGS_AND_GAPS.md` — limitations and future work.

### If you are a Google reviewer (Gmail OAuth)
1. `08_GMAIL_OAUTH.md` — scope, flow, data use.
2. `09_SECURITY_AND_PRIVACY.md` — data protection.
3. `13_VIDEO_SCRIPTS.md` (Video 4) — the verification video script.

---

## Document index

| # | File | What's inside |
|---|------|---------------|
| 00 | `00_PROJECT_OVERVIEW.md` | Plain-English overview, problem, name clarification, honest status, stack, 60-second tour, viva assessment |
| 01 | `01_FILE_BY_FILE_ANALYSIS.md` | Every meaningful file explained, with flags for dead/temporary code |
| 02 | `02_SYSTEM_ARCHITECTURE.md` | Architecture diagrams: system, auth, ingestion, AI, assistant, OAuth, realtime, deployment |
| 03 | `03_ALL_FEATURES.md` | 52 features, each with status, location, and limitations |
| 04 | `04_FRONTEND_EXPLAINED.md` | Screens, data flow, design system, assistant voice, conventions |
| 05 | `05_BACKEND_AND_APIS.md` | Full API reference + service layer + flows + config |
| 06 | `06_AI_AND_AGENTIC_SYSTEM.md` | The AI pipeline, routing, provider, prompts, context, attention, assistant phases — and the honest "not multi-agent" explanation |
| 07 | `07_DATABASE.md` | Collections, schemas, indexes, access patterns, isolation, lifecycle |
| 08 | `08_GMAIL_OAUTH.md` | OAuth flow, scope, poller, security, Google console setup, limitations |
| 09 | `09_SECURITY_AND_PRIVACY.md` | Auth, isolation, OAuth/webhook security, AI safety, privacy, weaknesses |
| 10 | `10_EXTERNAL_SERVICES.md` | MongoDB, Groq, Google, Meta, Brevo, Vercel — and what is *not* used |
| 11 | `11_TESTING_AND_DEPLOYMENT.md` | Test suites, rules, commands, deployment, coverage honesty |
| 12 | `12_LEARN_MY_PROJECT.md` | Beginner-friendly guided learning with a self-test |
| 13 | `13_VIDEO_SCRIPTS.md` | 60s, 3-min, 5–8-min, and Google OAuth video scripts |
| 14 | `14_VIVA_INTERVIEW_QA.md` | 70 interview questions with answers + trap questions |
| 15 | `15_FINDINGS_AND_GAPS.md` | README vs reality, dead code, gaps, legal review items, recommendations |

---

## Ground rules used to write this documentation

- Based on the **actual source code**, not on the README.
- Every feature is labelled **implemented / partial / planned / temporary / unverified**.
- Where the code and the marketing disagree, **the code wins** and the difference is recorded in `15_FINDINGS_AND_GAPS.md`.
- **No secrets, keys, tokens, or personal data** appear anywhere in these documents.
- No application code was modified to produce this documentation.
- All claims are **code-verified, not runtime-tested**.

---

## The one-paragraph summary

*Sift is a Next.js + FastAPI + MongoDB communication triage app. It ingests Gmail and WhatsApp messages through one shared pipeline, links threads deterministically, and analyses each message with a single rule-routed LLM call that produces priority, summary, action, tasks, and deadlines — with an explainable routing record and graceful pending-and-retry failure handling. A deterministic assistant (Kestrel/JARVIS) answers questions, navigates, and performs confirmed actions by voice or text. Everything is strictly user-scoped, tokens are encrypted or hashed, and the system keeps working when the AI is down.*
