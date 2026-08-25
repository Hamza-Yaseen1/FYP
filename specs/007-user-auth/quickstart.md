# Quickstart: Verify 007-user-auth

Manual walkthrough per slice. Prerequisites: MongoDB running, backend
(`uvicorn main:app --reload` in `backend/`), frontend (`npm run dev`),
fresh browser profile or incognito window.

## Slice 1 — Day 15: Signup

1. Open `http://localhost:3000/signup`.
2. Submit empty form → field-specific errors appear; no request succeeds.
3. Enter name, email `Test@Example.COM`, password `short` → rejected
   with minimum-length message.
4. Enter password `password123`, confirm `password124` → mismatch error.
5. Fix confirm to `password123`, submit → redirected to `/dashboard`
   signed in.
6. In Mongo shell: `db.users.find()` → one doc; `password_hash` present,
   NO plaintext password anywhere in the document.
7. Log out (clear cookies) and re-register the SAME email → clear
   "already exists" error. Register with `test@example.com` (lowercase)
   → also rejected (casing normalization works).
8. While signed out, visit `http://localhost:3000/dashboard` →
   redirected to `/login`.

## Slice 2 — Day 16: Login

1. Visit `/login`, enter wrong password → single generic
   "Invalid email or password" error.
2. Enter an unregistered email → identical generic error (no
   enumeration hint).
3. Enter correct credentials → dashboard loads with your data.
4. Close browser, reopen within session lifetime → still signed in.

## Slice 3 — Day 17: Protected data

1. Signed in as user A, simulate a message via the dashboard form →
   message appears with analysis as before (pipeline unchanged).
2. Check Mongo: the new message/task docs contain your `user_id`.
3. Delete `cai_token` cookie manually, refresh → redirected to login;
   calling any `/messages` endpoint without the cookie returns 401.

## Slice 4 — Day 18: Isolation proof

1. Register user B in a second browser profile.
2. B's dashboard shows ZERO of A's messages/tasks.
3. Copy one of A's message IDs from Mongo; as B, call
   `GET /messages/{A_message_id}` directly (curl/Postman) → **404**,
   no content leaked.
4. As B, attempt `DELETE /messages/{A_message_id}` → 404; A's data
   unchanged.
5. Run `pytest backend/tests/test_auth.py -q` → all green, including
   isolation tests.

## Slice 5 — Days 19–20: Polish

1. Navbar shows your name; logout button clears session and lands you
   on `/login`.
2. After logout, browser Back button never reveals workspace content.
3. Full constitution compliance checklist reviewed.

## Legacy data (one-time, optional)

```bash
python backend/scripts/assign_legacy_data.py --email hamza@example.com
```
Assigns all ownerless messages/tasks to that account — or delete legacy
docs instead. Ownerless docs are invisible to everyone either way.
