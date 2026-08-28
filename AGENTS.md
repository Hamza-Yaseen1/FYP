<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# my-app Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-08-28

## Active Technologies
- Python 3.13 + pytests, `unicodedata` (stdlib) for script detection (015-ai-orchestrator)
- MongoDB `messages` collection — `ai_analysis` gains a `routing` subdocument (015-ai-orchestrator)

- Python 3.13 + FastAPI, uvicorn, motor, pydantic, python-dotenv (014-whatsapp-webhook)
- MongoDB (`messages`, `connections`, `users` collections) - add a dedup index. Use documentation-driven design for day-by-day features (014-whatsapp-webhook)

## Recent Changes

- 014-whatsapp-webhook: Added Python 3.13 + FastAPI, uvicorn, pydantic, motor, python-dotenv
- 015-ai-orchestrator: Added Python 3.13 + rule-based AI orchestrator (routing, single-call gating, trivial-skip)

<!-- MANUAL ADDITIONS START -->
- 015-ai-orchestrator man: The single AI entry point is now `services/ai/orchestrate.py::process_message` (decide_routing -> analyze_message with internal gating -> attach `ai_analysis.routing`). Trivial messages short-circuit to deterministic defaults and no-content/media to a `skipped` stub — zero LLM calls on both. `routing` is attached on EVERY path (`llm_call_used=true` even on `pending` failures; a `_analyze_with_fallback` wrapper guards `analyze_message`/`get_provider` crashes). Routes/services must NEVER call `analyze_message` directly. Tests: never await motor under `asyncio.run` (use the TestClient loop or a fake collection). Debug/verification scripts can call `analyze_message` directly. Backend uses MongoDB Atlas (`MONGO_URI=mongodb+srv://` in `backend/.env`); auth is cookie-based (register/login set a session cookie — `httpx.AsyncClient` persists it). Standalone scripts `test_attention_pipeline.py`/`test_priority_integration.py` are era-stale (live-server auth-gated; shared-Atlas owner resolution) — kept as historical artifacts. `POST /messages` analyzes synchronously; `/webhooks/simulate` uses a background task (`ai_analysis: null` on the response). Full suite ~125 tests, needs 300s shell timeout.
<!-- MANUAL ADDITIONS END -->
