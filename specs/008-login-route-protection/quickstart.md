# Quickstart: Verify Login, Protected Routes & Auth UI

Manual verification script for `008-login-route-protection`. Executes the
spec's acceptance criteria AC-1…AC-10 and the DoD sweep. Authoritative for
this feature (constitution: manual testing mandatory for UI changes).

## Setup

1. Backend:
   - `cd backend` → ensure `.env` has `JWT_SECRET` and Mongo URI
   - `uvicorn main:app --reload --port 8000`
2. Frontend:
   - repo root → `npm run dev` → http://localhost:3000
3. Baseline checks:
   - `cd backend && pytest tests/test_auth.py -q` → all green
   - repo root → `npm run lint` clean, `npx tsc --noEmit` clean

You need TWO registered accounts for isolation checks (e.g., Hamza +
Ali) and one private/incognito window.

## A. Login flow (US1 / AC-1..AC-3) — Day 16

1. Open `/login` in incognito (logged out). Verify dark centered card,
   logo, labelled inputs.
2. Submit empty form → field-level errors under both fields, NO network
   request (check DevTools Network tab).
3. Enter invalid email format → "Enter a valid email address." inline.
4. Enter valid email + WRONG password → banner "Invalid email or
   password."; button showed "Signing in..." loading state while in
   flight; button not clickable during flight.
5. Register a fresh account (Ali). Log out. On `/login` type Ali's email
   + wrong password → SAME generic banner as step 4 (identical wording).
6. Log in with correct credentials → redirected to `/dashboard`.
7. Check DevTools → Application → Cookies: `cai_token` present,
   HttpOnly flagged. Local Storage/sessionStorage contain NO token.

## B. Route protection & session (US2 / AC-4..AC-9) — Day 17

1. In a NEW incognito window (no session): type `/dashboard`,
   `/inbox`, `/tasks`, `/attention`, `/connections`, `/settings` one by
   one → each redirects to `/login`. Record any miss.
2. Without session, call `curl -i http://localhost:8000/messages` → 401,
   JSON body, no message data. Repeat `/tasks`.
3. Log back in as Hamza → dashboard shows ONLY Hamza's messages/tasks.
4. Press F5 (refresh) on `/dashboard` → still signed in, same page, no
   bounce to login.
5. While logged in, open `/login` then `/signup` → each redirects to
   `/dashboard`.
6. In DevTools console try `document.cookie` → `cai_token` NOT visible.
7. Tamper test: edit the cookie value in DevTools (add junk), refresh →
   bounced to login; no private data flashes.
8. Click avatar menu → Log out → lands on `/login`; browser Back button
   does NOT reveal dashboard content.
9. Isolation: log in as Ali → zero Hamza records anywhere in UI; direct
   API `curl` with Ali's cookie against a known Hamza message id →
   not-found behavior, no content.

## C. Auth UI quality (US3 / AC-10)

1. Both pages side-by-side: identical typography, spacing, palette,
   button style; single primary action each; sibling link correct.
2. Password visibility toggle: click eye → characters shown; click again
   → masked; toggle keyboard-reachable (Tab order) with visible focus
   ring.
3. Tab through entire form: every control shows a clear focus indicator;
   pressing Enter submits.
4. Resize to ~360px width: no horizontal overflow, comfortable spacing,
   tappable targets. Repeat at 768px and 1280px.
5. Trigger an error (stop backend, submit) → human-readable
   "Something went wrong. Please try again." — never a stack trace.
6. Signup page: submit valid new user → works exactly as before restyle
   (account created, auto-signed-in, empty workspace).

## Definition of Done checklist

- [ ] pytest green (untouched suites)
- [ ] npm run lint clean; tsc clean
- [ ] AC-1…AC-10 all verified above
- [ ] Two-user isolation re-verified through UI
- [ ] Responsive at 360/768/1280px, keyboard operable
- [ ] Zero plaintext passwords/tokens in responses, cookies visible to JS, or logs
- [ ] Zero new dependencies added

## Production hardening notes (NOT this phase)

- Set cookie `secure=True` behind HTTPS at deployment.
- Consider rate limiting on `/auth/login` post-FYP.
