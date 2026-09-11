# Quickstart: Day 29 Security & Reliability Verification

**Feature**: `020-security-testing` | **Date**: 2026-09-11

How to run the Day 29 verification and reproducibility. Backend-only changes;
frontend is untouched (lint/vitest are run as a no-regression check only).

## Prerequisites

- Backend deps installed (`pip install -r backend/requirements.txt`).
- MongoDB reachable at `MONGO_URI` (default `mongodb://localhost:27017`).
- `.env` present in `backend/` (test suite sets `DB_NAME=communication_ai_test` itself).

## 1. Run the automated suites

### Backend (the Day 29 deliverable)

```powershell
# from the repo root
cd backend
python -m pytest tests/ -q
```

- Operational suite, uses `backend/tests/conftest.py` (TestClient + real MongoDB
  on `communication_ai_test`, wiped between tests).
- Expect: all 212 existing tests + new Day 29 tests green.
- Do NOT run plain `pytest` from the backend root — it collects era-stale
  standalone scripts (`test_ai_analysis.py`, `test_priority_integration.py`, …)
  that fail on `async def` collection / shared Atlas. They are historical
  artifacts: ignore them.
- First runs may be slow (~60–90s); use a 600s shell timeout.

### Frontend (no-regression check only — zero Day 29 changes)

```powershell
# from the repo root
npm run lint
npx vitest run
```

## 2. The four verification suites

| File | Proves |
|---|---|
| `backend/tests/test_security_testing.py` | Isolation matrix: A/B for connections + analytics; guessed-`ObjectId` reads → 404 with a body identical to non-existent; lists contain only own data |
| `backend/tests/test_dedup.py` | Dedupe: same `external_message_id` twice → 1 document; two users with the same key → independent docs; key-less exempt |
| `backend/tests/test_ai_reliability.py` | AI outage: message stored + `pending` + visible; `retry_pending_analyses()` completes the same document; failure never crashes ingest |
| `backend/tests/test_webhooks.py` (+ backfill) | Negative payloads rejected before processing; valid + signed accepted |

Targeted run:

```powershell
cd backend
python -m pytest tests/test_security_testing.py tests/test_dedup.py tests/test_ai_reliability.py tests/test_webhooks.py -q
```

## 3. Manual smoke checks (local dev)

Start backend (`uvicorn main:app --reload` in `backend/`) and frontend
(`npm run dev`), then:

1. **Isolation**: register User A and User B (two browsers/incognito). Create
   messages for both. As A, hit `GET http://localhost:8000/messages/{B's id}` →
   expect `404` (same body as a nonsense id). Check connections + analytics pages
   show only the logged-in user's data.
2. **Webhook rejection**: POST a body to `http://localhost:8000/webhooks/whatsapp`
   without `X-Hub-Signature-256` (or with a tampered one) via a REST client →
   `403 Invalid signature`. POST valid-signed-but-garbage JSON → `400`; message
   count unchanged.
3. **AI-outage**: temporarily comment out / invalidate the provider env key, then
   send a test message via `/webhooks/simulate`. The message appears on the
   dashboard with a pending indicator, not lost. Restore the key and run
   `retry_pending_analyses()` (or wait for the sweep) → the SAME message card now
   has completed analysis; no duplicate card.
4. **Dedupe**: POST the same signed Meta payload twice via a REST client → message
   count increases by exactly 1.

## 4. Known limitations (documented, not defects)

- Webhook owner resolution targets a single connected WhatsApp (first match);
  multi-number routing is a future amendment.
- Simulate and manual-create messages are exempt from dedupe (no provider id).

## 5. Definition of Done re-check

- [ ] All four verification suites green; full `backend/tests/` green
- [ ] Frontend lint + vitest green with zero Day 29 source changes
- [ ] Dedupe index is `{user_id, external_message_id}` (composite, partial)
- [ ] Pending messages are retried via `process_message` and updated in place
- [ ] No new dependencies, collections, or public endpoints