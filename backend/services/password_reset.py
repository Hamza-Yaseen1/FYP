"""Password reset tokens and Brevo transactional email delivery.

A reset token is a random, single-use secret. Only its SHA-256 hash is stored
on the user document, so a database leak cannot be replayed to take over an
account. Tokens expire after ``RESET_TOKEN_TTL_MINUTES`` and are removed as
soon as they are used.

Email is sent through Brevo's official REST API. The API key stays on the
backend and is never returned to the client or written to logs.
"""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from html import escape

import httpx

from database import users_collection

logger = logging.getLogger(__name__)

RESET_TOKEN_TTL_MINUTES = 30

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
try:
    BREVO_TIMEOUT_SECONDS = float(os.getenv("BREVO_TIMEOUT_SECONDS", "10"))
except ValueError:
    BREVO_TIMEOUT_SECONDS = 10.0

# Protection against email-bombing / burning through the email quota.
# A second request inside the window keeps the original token (still valid)
# and does not send another email.
RESET_REQUEST_COOLDOWN_SECONDS = int(
    os.getenv("RESET_REQUEST_COOLDOWN_SECONDS", "60")
)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _frontend_url() -> str:
    return (os.getenv("FRONTEND_URL") or "http://localhost:3000").rstrip("/")


def build_reset_link(token: str) -> str:
    return f"{_frontend_url()}/reset-password?token={token}"


def _as_utc(value: datetime | None) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


async def issue_reset_token(email: str) -> tuple[str | None, str | None]:
    """Create (or refresh) a reset token for ``email``.

    Returns ``(token, name)`` when a new token was issued, ``(None, name)`` when
    the account exists but is in the cooldown window, and ``(None, None)`` when
    no account matches. Never reveals which case occurred to the caller.
    """
    user = await users_collection.find_one({"email": email.lower()})
    if not user:
        return None, None

    now = datetime.now(timezone.utc)
    last_request = _as_utc(user.get("reset_requested_at"))
    if (
        last_request is not None
        and (now - last_request).total_seconds() < RESET_REQUEST_COOLDOWN_SECONDS
    ):
        return None, user.get("name")

    token = secrets.token_urlsafe(32)
    await users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "reset_token_hash": _hash_token(token),
                "reset_token_expires_at": now
                + timedelta(minutes=RESET_TOKEN_TTL_MINUTES),
                "reset_requested_at": now,
            }
        },
    )
    return token, user.get("name")


async def find_user_by_reset_token(token: str) -> dict | None:
    """Return the user matching a valid, unexpired reset token, else ``None``."""
    if not token:
        return None
    doc = await users_collection.find_one({"reset_token_hash": _hash_token(token)})
    if not doc:
        return None
    expires_at = _as_utc(doc.get("reset_token_expires_at"))
    if expires_at is None or expires_at <= datetime.now(timezone.utc):
        return None
    return doc


async def clear_reset_token(user_id) -> None:
    await users_collection.update_one(
        {"_id": user_id},
        {"$unset": {"reset_token_hash": "", "reset_token_expires_at": ""}},
    )


def _render_email(name: str | None, link: str) -> tuple[str, str]:
    safe_name = escape(name or "there")
    safe_link = escape(link)
    text = (
        f"Hi {name or 'there'},\n\n"
        "We received a request to reset your password. Use the link below to "
        f"choose a new one. It expires in {RESET_TOKEN_TTL_MINUTES} minutes and "
        "can only be used once.\n\n"
        f"{link}\n\n"
        "If you did not request this, you can safely ignore this email."
    )
    html = f"""\
<!doctype html>
<html>
  <body style="margin:0;padding:24px;background:#f5f4f2;font-family:ui-sans-serif,system-ui,-apple-system,'Segoe UI',sans-serif;color:#1c1b1a;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" style="max-width:480px;background:#ffffff;border-radius:16px;padding:32px;">
            <tr>
              <td>
                <h1 style="margin:0 0 8px;font-size:20px;">Reset your password</h1>
                <p style="margin:0 0 20px;font-size:14px;line-height:1.6;color:#5a5754;">
                  Hi {safe_name}, we received a request to reset your password.
                  This link expires in {RESET_TOKEN_TTL_MINUTES} minutes and can only be used once.
                </p>
                <p style="margin:0 0 24px;">
                  <a href="{safe_link}"
                     style="display:inline-block;background:#6d5efc;color:#ffffff;text-decoration:none;padding:12px 20px;border-radius:10px;font-size:14px;font-weight:600;">
                    Choose a new password
                  </a>
                </p>
                <p style="margin:0 0 8px;font-size:12px;color:#5a5754;">
                  If the button does not work, copy this link into your browser:
                </p>
                <p style="margin:0 0 20px;font-size:12px;word-break:break-all;color:#3f3c39;">
                  {safe_link}
                </p>
                <p style="margin:0;font-size:12px;color:#8a8683;">
                  If you did not request this, you can safely ignore this email.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""
    return html, text


async def _send_via_brevo(
    to_email: str,
    subject: str,
    html: str,
    text: str,
    api_key: str,
    sender_email: str,
) -> bool:
    """POST one transactional email to Brevo. Returns True on 2xx."""
    payload = {
        "sender": {"email": sender_email, "name": "Communication AI"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html,
        "textContent": text,
    }
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=BREVO_TIMEOUT_SECONDS) as client:
            res = await client.post(BREVO_API_URL, headers=headers, json=payload)
    except httpx.TimeoutException:
        logger.error("Brevo request timed out while sending a reset email.")
        return False
    except httpx.HTTPError:
        logger.exception("Brevo request failed while sending a reset email.")
        return False

    if not 200 <= res.status_code < 300:
        # Log the status only: the request body contains the reset token.
        logger.error(
            "Brevo rejected the reset email (HTTP %s).", res.status_code
        )
        return False
    return True


async def send_password_reset_email(
    to_email: str, name: str | None, token: str
) -> bool:
    """Send the reset link through Brevo. Never raises to the caller."""
    api_key = os.getenv("BREVO_API_KEY", "").strip()
    sender_email = os.getenv("EMAIL_FROM", "").strip()

    if not api_key:
        # Never log the reset link or token, even in development.
        logger.error(
            "BREVO_API_KEY is not set; cannot deliver password reset email."
        )
        return False
    if not sender_email:
        logger.error(
            "EMAIL_FROM is not set; cannot deliver password reset email."
        )
        return False

    html, text = _render_email(name, build_reset_link(token))
    return await _send_via_brevo(
        to_email,
        "Reset your password",
        html,
        text,
        api_key,
        sender_email,
    )
