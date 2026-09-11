# Development Journey — Communication AI Platform

**Student**: Hamza Yaseen
**Project**: Communication AI Platform ("Signal Desk")
**Window**: August 18 – September 2, 2026 (Days 1–25)

> This journey is reconstructed from the repository's git history, feature
> specs (`specs/`), plans, and documentation. Git commit dates are used where
> available; otherwise the stage order is inferred from the branch/spec
> sequence.

## Timeline

| Stage | Work Completed | Main Challenge | Solution |
| ----- | -------------- | -------------- | -------- |
| **Week 1 — Planning** (Days 1–3) | Core product definition; baseline spec; priority agent spec; project Constitution | Designing a simple yet reliable AI priority model | Documented 4 priority levels with evidence-based rules; "Needs Attention" concept |
| **Week 2 — Setup & Dashboard** (Day 8) | FastAPI backend, MongoDB (Motor), REST message endpoints, simulated messages, Next.js dashboard | MongoDB connection / environment configuration | Environment variables + documented `.env`; startup index creation |
| **Week 3 — AI Priority** (Days 9–12) | Groq provider, priority classification, priority badge + confidence UI, Priority Agent Constitution | AI analysis returning useless fallback instead of results | Fixed comprehensive prompt, API-key validation, detailed logging, safe defaults |
| **Week 4 — Tasks, Deadlines, Summaries** (Days 11–14) | Task model, task extraction, deadline detection, one-sentence summaries, attention flag | AI inventing tasks/deadlines (false positives, hallucinated dates) | Strict prompt rules: only explicit actions; preserve deadline wording; empty/null when uncertain; edge-case tests |
| **Week 5 — Complete AI Pipeline** (Day 14) | Recommended actions; single-call analysis; attention dashboard | Keeping one call reliable while returning ~6 fields; LLM rate limits | Structured JSON prompt; rate-limit detection; graceful `pending` fallback |
| **Week 6 — Auth & Isolation** (Days 15–18) | Registration/login/logout, JWT in httpOnly cookies, bcrypt, route protection, per-user data isolation | Secure session design; preventing cross-user data leaks | httpOnly cookie, constant-time password check, user-scoped queries; isolation tests |
| **Week 7 — Inbox, Tasks, Connections** (Days 19–22) | Priority tabs + filters + search, task status/snooze, connections architecture with AES token encryption | Efficient aggregation queries for filter counts | Indexed queries + aggregation pipelines; separate collections |
| **Week 8 — WhatsApp + AI Orchestration + Memory** (Days 23–25) | WhatsApp Cloud API webhook (HMAC verification + dedup), AI router/orchestrator, deterministic thread linking + agent memory | "Verification works but no messages arrive"; keeping memory cheap & safe | Documented Meta config; server-side signature verification; conservative rule-based linking + validated context updates |

---

## Biggest Achievements

1. **Full-stack application** — a complete, working product with a modern
   Next.js frontend, a FastAPI backend, and a MongoDB database, all integrated
   end-to-end.

2. **Unified single-call AI pipeline** — priority, tasks, deadlines, summary,
   and recommended action all produced by one LLM call per message,
   minimising latency and token cost while staying reliable.

3. **Cost-and-latency-optimising AI router** — a rule-based orchestrator that
   skips the LLM entirely for trivial or no-content messages (zero cost) and
   attaches an explainable routing record on every path.

4. **Secure WhatsApp Cloud API integration** — a real webhook with Meta
   verification handshake, HMAC-SHA256 signature verification, and
   deduplication, enabling genuine inbound messages.

5. **Lightweight agent memory** — deterministic thread linking plus validated,
   reason-named context updates that let the AI enrich earlier messages in a
   conversation — without expensive vector databases or RAG.

6. **Strict per-user data isolation** — every query scoped by authenticated
   user, verified by tests; combined with JWT + httpOnly-cookie auth.

7. **Automated testing** — 136 backend tests plus frontend component tests
   covering auth, isolation, webhooks, AI routing, and thread linking.

8. **Documentation-driven development** — spec/plan/tasks for every feature
   plus a governing Constitution that kept the project consistent and
   reviewable.

---

## Most Difficult Problems

1. **AI analysis failing silently** — the provider wasn't requesting all the
   fields the system needed; fixed by redesigning the prompt, validating the
   key, and adding comprehensive logging.

2. **LLM rate limits / daily token caps** — hits would block analysis; solved
   by detecting rate-limit errors and degrading gracefully to safe fallback
   values so messages are never lost.

3. **WhatsApp webhook "works but no messages"** — a configuration problem
   (subscription fields, one-directional traffic, unstable ngrok URL); solved
   by systematic troubleshooting and server-side hardening.

4. **Preventing AI hallucinations** — avoiding invented tasks and dates;
   solved with strict prompt rules ("preserve wording", "empty/null when
   uncertain") and edge-case tests.

5. **Async test reliability** — awaiting Motor inside `asyncio.run` caused
   flaky tests; solved by using the framework/TestClient loop or fake
   collections.

6. **Secure session + data isolation** — designing authentication that resists
   XSS and guarantees per-user privacy; solved with httpOnly cookies and
   user-scoped queries.

---

## Skills Developed

### Frontend
- Next.js 16 App Router, server & client components
- React hooks and component design (Base UI/shadcn + Tailwind CSS)
- Route-level middleware protection
- Frontend testing with Vitest + Testing Library

### Backend
- FastAPI routing, Pydantic validation, dependency injection
- Async programming with Python and Motor
- RESTful API design

### Database (MongoDB)
- Async driver (Motor), collections, indexes, aggregation pipelines
- Atomic updates, unique/partial indexes, deduplication

### AI / LLM
- Groq API integration
- Structured JSON prompting and reliable response parsing
- Prompt engineering and graceful failure handling
- Lightweight context / agent-memory design (deterministic linking + validation)

### Security
- JWT authentication, bcrypt hashing, httpOnly cookies
- HMAC webhook signature verification, AES token encryption
- OWASP-minded data isolation

### Process & Engineering
- Documentation-driven development (spec → plan → tasks)
- Version control with meaningful, feature-scoped commits
- Automated testing as a project convention
- Troubleshooting external integrations methodically
