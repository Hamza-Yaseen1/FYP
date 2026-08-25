# Tasks: Login, Protected Routes & Auth UI Polish

**Input**: Design documents from `/specs/008-login-route-protection/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Automated test tasks are included only as a conditional guard
(T011) per plan decision R6 — extend `backend/tests/test_auth.py` ONLY if
the audit finds an untested failure path. Manual verification via
quickstart.md is authoritative for UI work (constitution requirement).

**Organization**: Tasks are grouped by user story. Per plan.md's audit,
the Day 16/17 backend and route protection ALREADY EXIST and are tested;
US1 and US2 therefore verify and (only if needed) patch, while US3
contains the feature's real implementation work (dark-theme UI polish).

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Frontend: Next.js App Router at repo root (`app/`, `components/`, `lib/`, `middleware.ts`)
- Backend: FastAPI under `backend/`
- All verification scripts live in `specs/008-login-route-protection/quickstart.md`

---

## Phase 1: Setup (Baseline)

**Purpose**: Establish the green bar every later task must preserve

- [ ] T001 [P] Run backend auth suite and record pass count as regression baseline: `cd backend && pytest tests/test_auth.py -q`
- [ ] T002 [P] Run frontend static checks at repo root and record results: `npm run lint` and `npx tsc --noEmit`

**Checkpoint**: Baselines recorded; anything red here is pre-existing and must be reported before proceeding

---

## Phase 2: Foundational (Audit Existing Auth Surface)

**Purpose**: Confirm the as-built backend/middleware match contracts/auth.yaml and the spec BEFORE building UI on top

⚠️ Blocks all user story work: US1/US2 assume a verified base; US3 restyles pages whose behavior must not need changing later.

- [ ] T003 Audit the auth surface against specs/008-login-route-protection/contracts/auth.yaml with curl: register→201+Set-Cookie, login correct→200+user-without-hash, login wrong password AND unknown email→identical 401 body "Invalid email or password.", /auth/me→200 with cookie /401 without, logout→204 then 401; log any deviation in specs/008-login-route-protection/research.md under a new "Audit findings" heading
- [ ] T004 If T003 recorded deviations, apply the minimal fix in backend/routes/auth.py or backend/services/security.py (one behavior per commit-sized change); if none, mark T004 completed-as-N/A in the task list

**Acceptance criteria for T003**: zero deviations OR each deviation has a documented fix; wrong-password vs unknown-email responses are byte-identical.

**Checkpoint**: Auth surface verified as-built — user story implementation may begin

---

## Phase 3: User Story 1 - Log In with Email and Password (Priority: P1) 🎯 MVP

**Goal**: Prove the existing login flow satisfies every US1 acceptance scenario in the real UI (backend already built in 007).

**Independent Test**: Fresh incognito session → wrong password shows generic banner → correct credentials land on Hamza's own dashboard with HttpOnly cookie set and no token in script-accessible storage.

### Implementation for User Story 1

- [ ] T005 [US1] Execute specs/008-login-route-protection/quickstart.md section A steps 1–5 in the browser: empty-form submission blocked client-side with field errors and NO network request, invalid email flagged inline, wrong password shows exactly "Invalid email or password." banner, button shows loading text/state while in flight and cannot be double-clicked
- [ ] T006 [US1] Verify secure token handling per specs/008-login-route-protection/quickstart.md section A steps 6–7: successful login redirects to /dashboard showing only Hamza's data, `cai_token` cookie present with HttpOnly flag, token absent from localStorage/sessionStorage/document.cookie

**Acceptance criteria (story)**: AC-1, AC-2, AC-3 from spec.md all observed true; any miss becomes a fix task scoped to app/(auth)/login/page.tsx or lib/api.ts before checkpoint.

**Checkpoint**: MVP — a returning user can log in securely end-to-end

---

## Phase 4: User Story 2 - Locked Workspace (Priority: P2)

**Goal**: Prove every workspace page and data endpoint denies anonymous access, sessions survive refresh, and isolation holds — entirely through existing middleware + get_current_user.

**Independent Test**: Incognito window hits all six page URLs (all redirect to /login), curl hits endpoints (all 401 no data), signed-in refresh keeps state, tampered cookie bounces, two-user isolation shows zero cross-data.

### Implementation for User Story 2

- [ ] T007 [US2] In an incognito window type each protected URL (/dashboard, /inbox, /tasks, /attention, /connections, /settings) and verify every one redirects to /login per specs/008-login-route-protection/quickstart.md section B step 1; record any miss
- [ ] T008 [US2] Without a session cookie, curl `http://localhost:8000/messages` and `/tasks` and verify 401 JSON responses containing zero data per quickstart.md section B step 2
- [ ] T009 [US2] Signed-in checks per quickstart.md section B steps 3–5, 7–8: refresh preserves session and current page, /login and /signup redirect authenticated users to /dashboard, junk-edited cookie bounces to /login with no private content flash, logout ends session and browser Back reveals nothing
- [ ] T010 [US2] Re-run two-user isolation through UI plus direct API with Ali's cookie against a known Hamza message id per quickstart.md section B step 9; verify not-found behavior with no content leak
- [ ] T011 [US2] IF T007–T010 exposed a protection or isolation gap: add the missing case to the matching class in backend/tests/test_auth.py (TestProtectedSurface or TestIsolation), watch it fail, then fix the route/dependency in backend/routes/ or backend/dependencies.py; if no gap, mark completed-as-N/A

**Acceptance criteria (story)**: AC-4…AC-9 observed; SC-003/SC-004 hold (100% redirect/reject, zero cross-user records).

**Checkpoint**: Workspace provably locked; sessions durable; isolation intact

---

## Phase 5: User Story 3 - Auth Pages That Look Like a Real Product (Priority: P3) 🎨 Core build work

**Goal**: Transform /login and /signup into the shared dark-theme design system (spec FR-015…FR-021) without changing any working behavior.

**Independent Test**: Both pages render the centered dark card at 360/768/1280px with password toggle, focus rings, loading states, inline + banner errors — while signup still registers identically.

### Implementation for User Story 3

- [ ] T012 [P] [US3] Create components/auth/password-input.tsx: wrap components/ui/input.tsx with a lucide-react Eye/EyeOff toggle button positioned inside the field, aria-label switching between "Show password"/"Hide password", forwardRef support, value/onChange/type/disabled passthrough
- [ ] T013 [P] [US3] Restyle app/(auth)/layout.tsx as the shared dark shell: wrap children in `<div className="dark">`, deep neutral gradient background layer behind the centered max-w-sm column, retain Zap logo block with refined spacing
- [ ] T014 [US3] Polish app/(auth)/login/page.tsx onto the dark system: use PasswordInput for the password field, increase form rhythm to space-y-5+, add spinner icon inside the submit Button while `submitting`, keep all existing validation/error/router logic byte-identical (depends on T012, T013)
- [ ] T015 [US3] Apply the identical visual system to app/(auth)/signup/page.tsx: same PasswordInput, same spacing scale, same button treatment, same card composition; freeze behavior — same apiFetch("/auth/register") call, same validation function, same error mapping (depends on T012, T013)
- [ ] T016 [US3] Only if the gradient cannot be expressed with Tailwind utilities: add a single scoped utility to app/globals.css; otherwise mark completed-as-N/A (prefer zero CSS-file changes) (depends on T013)

**Acceptance criteria (story)**: side-by-side pages share identical tokens (AC per US3.5); toggle works by mouse and keyboard; no behavior diffs on submit.

**Checkpoint**: Both pages look intentional, modern, dark — flows unchanged

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Responsive, accessibility, and Definition-of-Done sweep across the touched files

- [ ] T017 [P] Responsive pass at ~360px, 768px, 1280px widths on both auth pages fixing any overflow/cramping in app/(auth)/layout.tsx and the two page files per quickstart.md section C step 4
- [ ] T018 Keyboard + focus pass per quickstart.md section C steps 2–3: Tab reaches every control with visible ring, Enter submits, eye toggle reachable and labeled
- [ ] T019 Error-path check with backend stopped: submit login → human-readable "Something went wrong. Please try again." banner, never a stack trace (section C step 5)
- [ ] T020 Final DoD sweep: re-run `cd backend && pytest tests/test_auth.py -q` (must equal T001 baseline), `npm run lint`, `npx tsc --noEmit`; tick every box in the specs/008-login-route-protection/quickstart.md Definition-of-Done checklist; confirm zero new dependencies were added

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately; T001 ∥ T002
- **Foundational (Phase 2)**: depends on Setup; BLOCKS all user stories (T004 depends on T003)
- **US1 (Phase 3)**: depends on Phase 2 — verifies login over the audited surface
- **US2 (Phase 4)**: depends on Phase 2; independent of US3; may run alongside US3 (different files) though sequential execution is fine solo
- **US3 (Phase 5)**: depends on Phase 2 (needs verified-stable behavior underneath); internally T012 ∥ T013 → T014/T015 (need T012+T013) → T016
- **Polish (Phase 6)**: depends on US3 completion (styles exist to inspect); T017–T019 after T015; T020 last

### User Story Dependencies

- **US1 (P1)**: standalone after Phase 2 — delivers demoable login immediately
- **US2 (P2)**: standalone after Phase 2 — no coupling to US1/US3 code paths (verification-only)
- **US3 (P3)**: standalone after Phase 2 — pure presentation layer over verified flows

### Within Each User Story

- Verification tasks execute quickstart.md sections in listed order
- Fixes (T004, T011) trigger only on observed failures — never speculative refactors
- US3: shared component before consumers; layout before page polish screenshots

### Parallel Opportunities

- T001 ∥ T002 (different toolchains)
- T012 ∥ T013 (different files)
- T017 ∥ T018 (independent passes, different concerns)
- US1 verification ∥ US3 component creation possible after Phase 2 (no file overlap)

---

## Parallel Example: User Story 3 kickoff

```text
Task: "T012 Create components/auth/password-input.tsx"
Task: "T013 Restyle app/(auth)/layout.tsx dark shell"
# Then sequentially: T014 → T015 → T016
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Phase 1 baselines → Phase 2 audit
2. Complete Phase 3 (US1 verification)
3. STOP and validate: demo login end-to-end
4. Ship if timeline pressure demands it

### Incremental Delivery

1. Setup + Foundational → trusted base
2. Add US1 → login demonstrable (MVP)
3. Add US2 → locked workspace demonstrable (security story complete)
4. Add US3 + Polish → evaluation-ready visuals
5. Each increment preserves the previous ones (behavior-frozen restyle)

### Solo Developer Strategy (FYP default)

Work strictly in ID order; the [P] marks are opportunities, not requirements. Expected effort concentrates in Phase 5 (~70% of the feature).

---

## Notes

- Conditional tasks (T004, T011, T016): if their trigger does not occur, mark `completed-as-N/A` rather than deleting — keeps the audit trail honest
- Signup behavior MUST NOT change in T015 (plan constraint; constitution DoD #4)
- Every manual observation goes straight into the quickstart.md checklist so T020 closes with evidence
- Commit after each task or logical group; never mix a fix with a restyle in one commit
