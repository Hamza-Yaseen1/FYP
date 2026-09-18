"""
Gmail OAuth 2.0 helpers + read-only API client (T011).

Handles: state JWT signing/verification, authorization URL building,
code exchange, token refresh, Google revoke, Gmail message listing/reading,
and MIME → normalized message conversion.

All Google calls go through httpx (direct REST). No Google SDK dependency.
"""
import asyncio
import logging
import os
import re
from base64 import urlsafe_b64decode
from datetime import datetime, timedelta, timezone
from email import policy
from email.parser import BytesParser
from typing import Any, Dict, List, Optional, Tuple

import httpx
import jwt

from database import db
from services.connection import ConnectionService
from utils.encryption import decrypt, encrypt

logger = logging.getLogger(__name__)

# ── constants ────────────────────────────────────────────────

GMAIL_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GMAIL_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"
GMAIL_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"

GMAIL_SCOPES = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_MAX_RESULTS = 20

# Signing secret for the short-lived OAuth state JWT.
# Same secret as the session cookie — the user already trusts us with it.
STATE_SIGNING_SECRET = os.getenv("JWT_SECRET", os.getenv("SESSION_SECRET", "dev-fallback"))
STATE_EXPIRY_SECONDS = 600  # 10 minutes

# Env-configured redirect URIs
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "http://localhost:8000/auth/google/callback",
)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


# ── OAuth state helpers (T011) ───────────────────────────────


def build_authorization_url(user_id: str) -> str:
    """Build the Google OAuth consent URL with a signed state JWT.

    The state binds the callback to *user_id* (CSRF protection + identity).
    Only `access_type=offline` + `prompt=consent` ensure a refresh_token
    is always issued (even on re-consent).
    """
    state = jwt.encode(
        {
            "sub": user_id,
            "purpose": "gmail_oauth",
            "jti": os.urandom(8).hex(),
            "exp": datetime.now(timezone.utc) + timedelta(seconds=STATE_EXPIRY_SECONDS),
        },
        STATE_SIGNING_SECRET,
        algorithm="HS256",
    )
    from urllib.parse import urlencode
    params = urlencode(
        {
            "response_type": "code",
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "scope": GMAIL_SCOPES,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )
    return f"{GMAIL_AUTH_URL}?{params}"


def verify_state(state: str) -> Optional[str]:
    """Decode a signed OAuth state JWT and return the owner user_id.

    Returns ``None`` on any failure (bad signature, wrong purpose, expired,
    malformed) — callers must treat None as "reject".
    """
    try:
        payload = jwt.decode(state, STATE_SIGNING_SECRET, algorithms=["HS256"])
    except (jwt.DecodeError, jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
    if payload.get("purpose") != "gmail_oauth":
        return None
    sub = payload.get("sub")
    if not sub:
        return None
    return sub


# ── Token exchange / refresh / revoke ────────────────────────


async def exchange_code(code: str) -> Tuple[str, str, int]:
    """Exchange an authorization code for access + refresh tokens.

    Returns (access_token, refresh_token, expires_in).

    Raises ValueError if Google rejects the code or the refresh_token
    is missing (which means the user hasn't actually consented yet).
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GMAIL_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
    if resp.status_code != 200:
        logger.warning("Google token exchange failed (%s): %s", resp.status_code, resp.text)
        raise ValueError(f"Google token exchange failed: {resp.status_code}")
    body = resp.json()
    access_token = body.get("access_token", "")
    refresh_token = body.get("refresh_token", "")
    expires_in = body.get("expires_in", 3600)
    if not refresh_token:
        raise ValueError("No refresh_token in Google response — user may have skipped consent")
    return access_token, refresh_token, expires_in


async def get_gmail_email_display(access_token: str) -> Optional[str]:
    """Best-effort fetch of the connected Gmail address (display only)."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                GMAIL_TOKENINFO_URL,
                params={"access_token": access_token},
            )
        if resp.status_code == 200:
            return resp.json().get("email")
    except Exception:
        logger.debug("Could not fetch email display from tokeninfo", exc_info=True)
    return None


async def refresh_access_token(
    refresh_token_encrypted: str,
    connection_id: str,
    user_id: str,
) -> Optional[str]:
    """Use the refresh_token to obtain a fresh access_token.

    On success the new encrypted access_token + expiry are written to the DB
    via ConnectionService.update_gmail_tokens(). Returns the new raw
    access_token, or None on failure (caller should set error status).

    ``refresh_token_encrypted`` must already be encrypted (stored in DB).
    """
    refresh_token = decrypt(refresh_token_encrypted)
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GMAIL_TOKEN_URL,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
    if resp.status_code != 200:
        logger.warning(
            "Google token refresh failed (%s) for connection %s: %s",
            resp.status_code,
            connection_id,
            resp.text,
        )
        return None
    body = resp.json()
    new_access = body.get("access_token", "")
    expires_in = body.get("expires_in", 3600)
    token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)
    new_encrypted_access = encrypt(new_access)

    svc = ConnectionService(db)
    await svc.update_gmail_tokens(connection_id, user_id, new_encrypted_access, token_expires_at)
    return new_access


async def revoke_google_access(refresh_token_encrypted: str) -> bool:
    """Best-effort revocation of the Google OAuth grant."""
    try:
        refresh_token = decrypt(refresh_token_encrypted)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GMAIL_REVOKE_URL,
                params={"token": refresh_token},
            )
        if resp.status_code == 200:
            logger.info("Google token revoked successfully")
            return True
        logger.warning("Google revoke returned %s", resp.status_code)
    except Exception:
        logger.warning("Google revoke failed", exc_info=True)
    return False


# ── Gmail API: ensure fresh token + list/get messages ────────


async def _ensure_access_token(
    connection_doc: dict,
    connection_id: str,
    user_id: str,
) -> Optional[str]:
    """Return a valid access_token, refreshing if needed.

    Returns None if the token cannot be refreshed (caller must set error).
    """
    raw_access = decrypt(connection_doc["access_token"])
    token_expires_at = connection_doc.get("token_expires_at")
    if not token_expires_at or datetime.now(timezone.utc) >= token_expires_at:
        logger.info("Access token expired or missing expiry, refreshing for %s", connection_id)
        refreshed = await refresh_access_token(
            connection_doc["refresh_token"], connection_id, user_id
        )
        if refreshed is None:
            return None
        return refreshed
    return raw_access


async def list_new_message_ids(
    access_token: str,
    after_epoch: Optional[int] = None,
    max_results: int = GMAIL_MAX_RESULTS,
) -> List[str]:
    """List Gmail message IDs fetched after *after_epoch* (Unix seconds).

    Uses ``q=after:<epoch>`` for read-only compatible date filtering.
    """
    q_parts: List[str] = []
    if after_epoch is not None:
        q_parts.append(f"after:{after_epoch}")
    query = " ".join(q_parts) if q_parts else ""
    params: Dict[str, Any] = {"maxResults": max_results}
    if query:
        params["q"] = query
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GMAIL_API_BASE}/users/me/messages",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
    if resp.status_code != 200:
        logger.warning("Gmail list failed (%s): %s", resp.status_code, resp.text)
        return []
    return [m["id"] for m in resp.json().get("messages", [])]


async def get_message_raw(access_token: str, message_id: str) -> Optional[dict]:
    """Fetch a single Gmail message in raw (MIME) format."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GMAIL_API_BASE}/users/me/messages/{message_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"format": "raw"},
        )
    if resp.status_code != 200:
        logger.warning("Gmail get message %s failed (%s)", message_id, resp.status_code)
        return None
    return resp.json()


# ── MIME → normalized message (T011/T019) ────────────────────


def normalize_email(raw: dict) -> Optional[dict]:
    """Convert a raw Gmail message (format=raw) to the canonical ingest format.

    Returns a dict with source, sender, content, subject,
    external_message_id, and received_at — or None if parsing fails
    entirely (should not happen; callers should handle None).

    Attachments are ignored (Constitution Day 26: receive-only, no
    attachments). Body extraction: text/plain preferred, HTML stripped to
    plain text as fallback, empty string if neither.

    The Gmail API returns the base64url MIME at the TOP-LEVEL ``raw``
    field for ``format=raw``; the legacy ``payload.raw`` key (used by early
    test doubles and some proxies) is honoured as a fallback.
    """
    message_id = raw.get("id")
    if not message_id:
        return None

    raw_payload = raw.get("payload", {})
    raw_source = raw.get("raw") or raw_payload.get("raw", "")
    raw_bytes = urlsafe_b64decode(raw_source or "")
    if not raw_bytes:
        # Fallback: construct minimal dict from headers
        headers = {h["name"].lower(): h["value"] for h in raw_payload.get("headers", [])}
        return {
            "sender": _clean_sender(headers.get("from", "")),
            "content": "",
            "subject": headers.get("subject", ""),
            "external_message_id": message_id,
        }

    msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
    sender = _clean_sender(str(msg.get("From", "")))
    subject = str(msg.get("Subject", ""))

    # Body extraction: prefer text/plain, fall back to text/html stripped
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = str(part.get_content_type())
            disp = str(part.get("Content-Disposition", ""))
            if "attachment" in disp:
                continue
            if ct == "text/plain":
                body = str(part.get_content())
                break
            if ct == "text/html" and not body:
                body = _strip_html(str(part.get_content()))
    else:
        ct = str(msg.get_content_type())
        if ct == "text/plain":
            body = str(msg.get_content())
        elif ct == "text/html":
            body = _strip_html(str(msg.get_content()))

    return {
        "sender": sender,
        "content": body,
        "subject": subject,
        "external_message_id": message_id,
    }


def _clean_sender(raw_from: str) -> str:
    """Strip surrounding quotes the email parser adds to display names.

    ``"Dr. Smith" <smith@uni.edu>`` → ``Dr. Smith <smith@uni.edu>``
    """
    s = raw_from.strip()
    if s.startswith('"') and '"' in s[1:]:
        idx = s.index('"', 1)
        name = s[1:idx]
        rest = s[idx + 1:].strip()
        return f"{name} {rest}" if rest else name
    return s


def _strip_html(html: str) -> str:
    """Minimal HTML tag stripping — no external deps."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ── High-level: ensure connection is fresh + return access_token ──


async def ensure_fresh_connection(connection_doc: dict, connection_id: str, user_id: str) -> Optional[str]:
    """Return a usable access_token for the connection, refreshing if needed.

    Returns None if the token is irrecoverably invalid (caller should
    set the connection to error status).
    """
    return await _ensure_access_token(connection_doc, connection_id, user_id)


# ── Poller (T021/T022) ──────────────────────────────────────


async def poll_connected_gmail() -> None:
    """One-shot poll: iterate all connected Gmail users, fetch new emails,
    normalize, and ingest. Called in a loop from the lifespan task.

    Per-user errors are isolated — a failure for one connection does not
    affect others or block the poll loop.
    """
    svc = ConnectionService(db)
    cursor = svc.collection.find({"provider": "gmail", "status": "connected"})
    async for conn_doc in cursor:
        conn_id = str(conn_doc["_id"])
        user_id = conn_doc["user_id"]
        try:
            await _poll_one_connection(conn_doc, conn_id, user_id)
        except Exception:
            logger.exception("Poll failed for connection %s — skipping", conn_id)


async def _poll_one_connection(conn_doc: dict, conn_id: str, user_id: str) -> None:
    """Fetch new emails for one Gmail connection and ingest them."""
    svc = ConnectionService(db)
    
    access_token = await _ensure_access_token(conn_doc, conn_id, user_id)
    if access_token is None:
        logger.warning("Cannot refresh token for %s — marking error", conn_id)
        await svc.set_connection_error(conn_id, user_id)
        return

    # Watermark: use last_fetched_at, default to connection creation − 1h
    last_fetched = conn_doc.get("last_fetched_at")
    if last_fetched is None:
        created = conn_doc.get("created_at", datetime.now(timezone.utc))
        if isinstance(created, datetime):
            last_fetched = created - timedelta(hours=1)
        else:
            last_fetched = datetime.now(timezone.utc) - timedelta(hours=1)
    after_epoch = int(last_fetched.timestamp()) if isinstance(last_fetched, datetime) else int(last_fetched)

    message_ids = await list_new_message_ids(access_token, after_epoch=after_epoch)
    if not message_ids:
        return

    from services.webhook_ingest import ingest_message

    # Fetch + ingest each message concurrently, bounded so a burst of new
    # mail cannot open a full-second wave of parallel Google calls. Errors
    # are isolated per message and never abort the rest of the batch.
    sem = asyncio.Semaphore(5)

    async def _fetch_and_ingest(mid: str) -> None:
        try:
            async with sem:
                raw = await get_message_raw(access_token, mid)
                if raw is None:
                    return
                norm = normalize_email(raw)
                if norm is None:
                    return
                await ingest_message(
                    user_id=user_id,
                    source="gmail",
                    sender=norm["sender"],
                    content=norm["content"],
                    external_message_id=norm["external_message_id"],
                    subject=norm.get("subject") or None,
                )
        except Exception:
            logger.exception(
                "Gmail fetch/ingest failed for message %s — skipping", mid
            )

    await asyncio.gather(*(_fetch_and_ingest(mid) for mid in message_ids))

    # Advance watermark
    now = datetime.now(timezone.utc)
    await svc.collection.update_one(
        {"_id": conn_doc["_id"]},
        {"$set": {"last_fetched_at": now, "updated_at": now}},
    )
    logger.info(
        "Poll complete for connection %s: %d messages processed",
        conn_id,
        len(message_ids),
    )
