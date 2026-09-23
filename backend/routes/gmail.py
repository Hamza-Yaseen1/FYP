"""
Gmail OAuth endpoints (T012-T013).

GET  /connections/gmail/auth-url   → returns the Google consent URL
GET  /connections/gmail/callback   → handles the OAuth redirect, stores tokens
GET  /auth/google/callback         → alias of the callback (matches the
                                     GOOGLE_REDIRECT_URI used in backend/.env)
"""
import logging
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from database import db
from dependencies import get_current_user
from services.connection import ConnectionService
from services.gmail import (
    FRONTEND_URL,
    build_authorization_url,
    exchange_code,
    get_gmail_email_display,
    verify_state,
)
from services.gmail import _poll_one_connection
from utils.encryption import encrypt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connections/gmail", tags=["gmail-oauth"])
google_router = APIRouter(prefix="/auth/google", tags=["gmail-oauth"])


@router.get("/auth-url")
async def auth_url(current_user: dict = Depends(get_current_user)):
    """Return the Google OAuth consent URL for the logged-in user.

    The URL contains a signed, short-lived state JWT binding the
    callback to this user (CSRF + identity).
    """
    user_id = str(current_user["_id"])
    url = build_authorization_url(user_id)
    return {"auth_url": url}


@router.post("/refresh")
async def refresh_gmail(current_user: dict = Depends(get_current_user)):
    """Trigger an immediate full Gmail resync for the current user.

    Runs the poller right now with a forced full INBOX scan (no ``after:``
    time filter), so older emails the narrow watermark may have skipped are
    picked up. The {user_id, external_message_id} unique index keeps already
    stored emails from being duplicated.

    Returns what the poll actually found vs saved.
    """
    user_id = str(current_user["_id"])
    svc = ConnectionService(db)
    conn = await svc.collection.find_one(
        {"user_id": user_id, "provider": "gmail", "status": "connected"}
    )
    if conn is None:
        raise HTTPException(status_code=404, detail="No connected Gmail account")

    conn_id = str(conn["_id"])
    logger.info("Manual Gmail refresh triggered for user %s", user_id)
    summary = await _poll_one_connection(
        conn, conn_id, user_id, force_full_scan=True
    )
    return {"connection_id": conn_id, **summary}


async def _run_callback(code: str, state: str, error: str) -> RedirectResponse:
    """Shared Google OAuth callback handler (both /connections/gmail/callback
    and /auth/google/callback delegate here)."""
    frontend_base = FRONTEND_URL.rstrip("/")

    # ── Error from Google ──
    if error:
        logger.warning("Google returned error: %s", error)
        return RedirectResponse(f"{frontend_base}/connections?gmail=error")

    # ── Verify state ──
    user_id = verify_state(state)
    if user_id is None:
        logger.warning("Invalid or expired OAuth state")
        return RedirectResponse(f"{frontend_base}/connections?gmail=error")

    # ── Exchange code ──
    try:
        access_token, refresh_token, expires_in = await exchange_code(code)
    except Exception as exc:
        logger.warning("Token exchange failed for user %s: %s", user_id, exc)
        return RedirectResponse(f"{frontend_base}/connections?gmail=error")

    # ── Best-effort email display ──
    gmail_email = await get_gmail_email_display(access_token)

    # ── Encrypt + store ──
    token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)
    encrypted_access = encrypt(access_token)
    encrypted_refresh = encrypt(refresh_token)

    svc = ConnectionService(db)
    await svc.upsert_gmail_connection(
        user_id=user_id,
        access_token=encrypted_access,
        refresh_token=encrypted_refresh,
        token_expires_at=token_expires_at,
        gmail_email=gmail_email,
    )

    logger.info("Gmail connected for user %s (email=%s)", user_id, gmail_email)
    return RedirectResponse(f"{frontend_base}/connections?gmail=connected")


@router.get("/callback")
async def callback(code: str = "", state: str = "", error: str = ""):
    """Handle the Google OAuth redirect.

    This endpoint is NOT cookie-authenticated — the signed ``state``
    carries the user identity. On success it redirects to the frontend
    Connections page with ``?gmail=connected`` (or ``?gmail=error``).
    """
    return await _run_callback(code, state, error)


@google_router.get("/callback")
async def google_callback(code: str = "", state: str = "", error: str = ""):
    """Alias of /connections/gmail/callback — matches the Authorized redirect
    URI configured in backend/.env (GOOGLE_REDIRECT_URI=.../auth/google/callback)."""
    return await _run_callback(code, state, error)
