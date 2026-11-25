# 15 — Findings & Gaps

> Everything that does not match, is unfinished, is risky, or is worth knowing before you present Sift. This is the most important document to read before a viva, a supervisor meeting, or any public claim.

---

## 1. README vs reality (highest priority)

The `README.md` overstates several features. If an examiner reads it and then inspects the code, you need to have already acknowledged these.

| README / marketing claim | Reality in code | Action |
|--------------------------|-----------------|--------|
| "Multi-agent AI system" | **One** LLM call with rule-based routing; the 5 "agents" are outputs, not separate agents. | Reframe as "rule-routed, explainable AI". |
| "Autonomous" | Nothing runs autonomously beyond a retry sweep; all AI is triggered by messages/commands. | Remove "autonomous" from any description. |
| "Sign in with Google" | Not implemented. Google OAuth is only for Gmail connect. | Do not claim it. |
| "AI writes and sends replies" | A draft is shown in the assistant panel; there is **no send path**. | Say "drafts only". |
| "Sentiment analysis" | Not a feature; intent exists only inside the assistant. | Remove the claim. |
| "Analytics: 7 / 30 / 90 days" | Only `day`, `week`, `month`. | Correct to three periods. |
| "Priority levels incl. Low" | Backend supports `low`, but the frontend `lib/priority.ts` only has urgent/important/normal. | Note the UI omits Low. |
| "Encrypted with Fernet" (if stated) | Tokens are **AES-CBC** via `utils/encryption.py`. | Correct to AES. |
| "Manual task creation" | Tasks come from AI extraction or the assistant; there is no create-task form in the UI. | Clarify. |
| "Email notifications" | Not implemented; only password-reset email exists. | Remove or mark planned. |
| "LinkedIn integration" | Shown as "coming soon" only. | Keep as roadmap. |

> Recommendation: rewrite the README's feature list to match `03_ALL_FEATURES.md`, or add a "status" column. A README that matches the code is far more defensible.

---

## 2. Brand-name inconsistency

- `lib/brand.ts` defines `BRAND_NAME = "Sift"` and `ASSISTANT_NAME = "Kestrel"`.
- The backend and many file names still say **JARVIS** and **Signal Desk**.
- `localizeAssistantReply()` rewrites these at display time, so users see Sift/Kestrel — but the internal names leak into code, docs, prompts, and this repository's own AGENTS changelog.

**Impact:** confusing for new readers and reviewers. **Action:** either finish the rename or add a short "naming" note at the top of the README (this documentation already explains it in `00_PROJECT_OVERVIEW.md`).

---

## 3. Documentation drift

| Document | Problem |
|----------|---------|
| `AI-FIX-SUMMARY.md` | Describes a fix to the **OpenAI** provider, which is now **dead code**. The active path is Groq. Stale. |
| `AGENTS.md` | Very long changelog. It documents phases up to "025-jarvis-tts" but the code contains an additional **Phase 6** of the assistant that is not described there. |
| `docs/day1-core-product.md` | Mentions a 4th priority ("Low") and an "urgency score 0–100" that are **not** in the current frontend or API surface. Conceptual only. |
| `README.md` | See §1. |
| Root `*.md` (SPEC/PLAN/etc.) | Mixed-era; some describe features that changed. |

**Action:** add a "docs status" note or archive stale docs so reviewers aren't misled.

---

## 4. Dead code & temporary artifacts

| Item | Location | Issue |
|------|----------|-------|
| `OpenAIProvider` | `backend/services/ai/providers/openai.py` | Unused; factory always returns Groq. |
| `components/TaskList.tsx` | root `components/` | Older duplicate, superseded by `components/tasks/TaskList.tsx`; not imported. |
| `BulkTestButton` | `components/BulkTestButton.tsx` + dashboard page | **TEMPORARY** load-testing UI still shipped. |
| `openai` dependency | `backend/requirements.txt` | Only needed by dead code. |
| `ai_analysis` collection reference | `backend/database.py` | The analysis is stored inline; the collection reference is legacy. |
| Era-stale scripts | `backend/test_*.py` (5 files) | Not part of the suite; will "fail" if run. |
| No-op UI controls | `components/SettingsClient.tsx` | "Sign out everywhere" and "Delete account" do nothing. |
| "Remember me" checkbox | `app/(auth)/login/page.tsx` | Cosmetic only. |
| `utils/__init__.py` | `backend/utils/` | Missing (namespace package). Add a marker if packaging. |

**Action:** remove or clearly label each before submission/demo.

---

## 5. Functional gaps

| Gap | Detail | Severity |
|-----|--------|----------|
| No login rate limiting | Only password-reset has a cooldown. Brute-force protection absent. | High |
| No email verification | Accounts can be created with any email. | Medium |
| Stateless sessions | No server-side revocation; "logout everywhere" is impossible as-is. | Medium |
| In-memory assistant context | Lost on restart; not shared across instances. | Medium |
| In-process background loops | Gmail poller + retry sweep need a long-lived process. | Medium |
| In-process realtime | WebSocket fan-out won't work across multiple instances. | Medium |
| No account deletion flow | Deletion is manual by email. | Medium |
| No automated retention | No data expiry policy in code. | Medium (legal) |
| Attachments ignored | Only text bodies analysed. | Low |
| No notifications | Preferences stored but nothing sends them. | Low |
| No export | Users cannot export their data. | Low |
| Only 3 analytics periods | No custom range. | Low |
| UI omits "Low" priority | Backend supports it; frontend doesn't show it. | Low |

---

## 6. Legal / compliance review items

These are flagged **inside the Privacy Policy and Terms** (`reviewNotes` arrays) and must be resolved before any public claim:

1. **Legal entity & jurisdiction** — the Terms contain a placeholder (`[jurisdiction to be confirmed — likely Pakistan…]`).
2. **Retention periods** — no concrete schedule for messages/tasks/connections/logs.
3. **Backup retention** — Atlas backup policy not documented.
4. **Children's age threshold** — placeholder; no age gate.
5. **Source-code licence** — no LICENSE file; ownership/licensing unclear.
6. **Post-FYP availability** — is the service going to stay online after the project ends? Not stated.
7. **Google verification / CASA status** — not started; blocks real Gmail users.
8. **Subprocessor DPAs** — Groq, Brevo, Atlas, Vercel, Google, Meta are named but no DPAs exist.
9. **GDPR rights process** — the policy references rights but the actual process is "email us".

**Action:** either resolve these or keep the review callouts visible so the honesty is explicit.

---

## 7. Operational risks

- **Brevo live sending unverified** — the API key type and sender verification were not confirmed in this repo. Password reset may silently fail.
- **`GROQ_MODEL` availability** — model names change; `llama-3.1-8b-instant` was not available on some accounts (404). The default Qwen model can consume budget on reasoning (mitigated by `reasoning_effort="none"`).
- **Cross-site cookies** — with frontend and backend on different Vercel domains, `COOKIE_SAMESITE=None` + `COOKIE_SECURE=true` are required or login will appear to fail.
- **DNS/SRV timeouts** — mitigated by pinned resolvers, but a flaky network can still slow startup.
- **Single instance assumptions** — realtime and background loops assume one process.
- **No health/alerting** — `GET /health` exists but nothing monitors it.

---

## 8. AI-quality and honesty risks

- **Overclaiming "agentic"** is the biggest reputational risk in a viva. Use the accurate framing every time.
- **Language coverage** — prompts include Arabic examples, but quality across languages is not systematically tested.
- **Hallucination** — mitigated (strict prompts, deterministic attention/deadlines, verbatim-only context) but not eliminated.
- **Cost control** — free-tier limits are the binding constraint; the circuit breaker and low token caps help but a burst can still stall analyses.
- **Evaluation** — there is no measured accuracy benchmark for priority/summary/task extraction. If asked "how accurate is it?", the honest answer is "not formally measured; we rely on prompt discipline, deterministic rules, and human override".

---

## 9. Test-coverage gaps

- No end-to-end browser tests (no Playwright/Cypress).
- No accessibility testing (no axe).
- No load/performance testing (beyond the temporary button).
- External calls are always mocked — no integration test against real Google/Brevo/Meta.
- Voice behaviour is faked in jsdom — not tested on real devices.
- Deployment/runtime behaviour is untested.

All security and AI claims in this documentation are **code-verified, not runtime-verified**.

---

## 10. Prioritised recommendations

**Before submission / demo (must do):**
1. Rewrite the README feature list to match reality (or add status labels).
2. Remove or hide `BulkTestButton` and the `/test/bulk-messages` surface.
3. Remove dead code (`openai.py`, duplicate `TaskList.tsx`) or clearly label it.
4. Fix the `SettingsClient` no-op controls (disable + label, or implement).
5. Rehearse the honest "not multi-agent" framing.

**Before any public launch (should do):**
6. Add login rate limiting and email verification.
7. Complete Google verification + CASA for Gmail.
8. Verify Brevo live sending.
9. Resolve the legal review items (entity, retention, licence, age).
10. Add security headers (CSP/HSTS) and a documented retention schedule.

**Nice to have:**
11. Move background work to a worker and persist assistant context.
12. Add push notifications and data export.
13. Add end-to-end and accessibility tests.
14. Finish the JARVIS→Kestrel rename in code.

---

## 11. The "one thing" to remember

If an examiner asks the hardest question — *"What is the weakest part of this project?"* — the best answer is:

> *"The framing, not the engineering. The code is a solid, well-tested, deterministic-first AI pipeline with graceful degradation and strong isolation. But the marketing called it a multi-agent autonomous system, which it isn't — it's one rule-routed LLM call. If I were to redo it, I'd describe it accurately from day one and spend the saved time on rate limiting and Google verification."*
