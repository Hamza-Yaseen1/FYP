import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

TOKEN_COOKIE_NAME = "cai_token"
TOKEN_EXPIRY_DAYS = 7

# Short-lived, purpose-scoped tokens used only for the development WebSocket
# handshake when the browser cannot be relied on to send the session cookie
# (cross-origin/cross-port local dev). They can never be used as a REST session
# (see `decode_token`, which rejects any token carrying a `purpose` claim).
WS_TOKEN_EXPIRY_SECONDS = 120
WS_TOKEN_PURPOSE = "ws"

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET is not set. Add it to backend/.env (see .env.example)."
    )


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(days=TOKEN_EXPIRY_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None
    # Purpose-scoped tokens (e.g. the short-lived WebSocket token) are never
    # valid session tokens, so a token minted for one surface cannot be
    # replayed against the REST API.
    if payload.get("purpose"):
        return None
    return payload.get("sub")


def create_ws_token(user_id: str) -> str:
    """Mint a short-lived token used only to authenticate a WebSocket.

    Deliberately separate from the session token: it expires quickly, carries a
    ``purpose`` claim, and cannot be used as a session cookie.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "purpose": "ws",
        "iat": now,
        "exp": now + timedelta(seconds=WS_TOKEN_EXPIRY_SECONDS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_ws_token(token: str) -> str | None:
    """Decode a WebSocket token; returns ``None`` unless purpose == ``ws``."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None
    if payload.get("purpose") != "ws":
        return None
    return payload.get("sub")
