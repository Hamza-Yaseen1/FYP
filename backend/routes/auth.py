from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response

from database import users_collection
import os
from dependencies import get_current_user
from models.user import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserCreate,
    UserLogin,
    user_doc_to_response,
)
from services import password_reset
from services.security import (
    TOKEN_COOKIE_NAME,
    TOKEN_EXPIRY_DAYS,
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

FORGOT_PASSWORD_MESSAGE = (
    "If an account with that email exists, a password reset link has been sent."
)


def _set_session_cookie(response: Response, token: str) -> None:
    cookie_secure = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    cookie_samesite = os.getenv("COOKIE_SAMESITE", "lax" if not cookie_secure else "none").lower()
    # For cross-site cookies, SameSite=None requires Secure=True
    if cookie_samesite == "none":
        cookie_secure = True
    response.set_cookie(
        key=TOKEN_COOKIE_NAME,
        value=token,
        max_age=TOKEN_EXPIRY_DAYS * 24 * 3600,
        httponly=True,
        samesite=cookie_samesite,
        secure=cookie_secure,
        path="/",
    )


@router.post("/register", status_code=201)
async def register(payload: UserCreate, response: Response):
    email = payload.email.lower()

    existing = await users_collection.find_one({"email": email})
    if existing:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    doc = {
        "name": payload.name.strip(),
        "email": email,
        "password_hash": hash_password(payload.password),
        "created_at": datetime.now(timezone.utc),
    }
    result = await users_collection.insert_one(doc)
    doc["_id"] = result.inserted_id

    _set_session_cookie(response, create_access_token(str(result.inserted_id)))
    return user_doc_to_response(doc)


@router.post("/login")
async def login(payload: UserLogin, response: Response):
    email = payload.email.lower()
    user = await users_collection.find_one({"email": email})

    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    _set_session_cookie(response, create_access_token(str(user["_id"])))
    return user_doc_to_response(user)


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    """Request a reset link. Always returns the same message.

    Whether the email is registered, whether it was just requested, and whether
    Brevo delivery succeeded are all kept out of the response so the endpoint
    cannot be used to enumerate accounts.
    """
    token, name = await password_reset.issue_reset_token(payload.email)
    if token:
        await password_reset.send_password_reset_email(
            payload.email.lower(), name, token
        )
    return {"message": FORGOT_PASSWORD_MESSAGE}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest):
    user = await password_reset.find_user_by_reset_token(payload.token)
    if not user:
        raise HTTPException(
            status_code=400,
            detail=(
                "This reset link is invalid or has expired. "
                "Please request a new one."
            ),
        )

    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_hash": hash_password(payload.password)}},
    )
    # Single-use: remove the token after the password has been changed.
    await password_reset.clear_reset_token(user["_id"])
    return {"message": "Your password has been reset. You can now sign in."}


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return user_doc_to_response(current_user)


@router.post("/logout", status_code=204)
async def logout(response: Response):
    # No auth required: the cookie must be cleared even when the token
    # is expired or invalid, otherwise the user can never sign out.
    cookie_secure = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    cookie_samesite = os.getenv("COOKIE_SAMESITE", "lax" if not cookie_secure else "none").lower()
    if cookie_samesite == "none":
        cookie_secure = True
    response.delete_cookie(
        key=TOKEN_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite=cookie_samesite,
        secure=cookie_secure,
    )
