from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response

from database import users_collection
from dependencies import get_current_user
from models.user import UserCreate, UserLogin, user_doc_to_response
from services.security import (
    TOKEN_COOKIE_NAME,
    TOKEN_EXPIRY_DAYS,
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=TOKEN_COOKIE_NAME,
        value=token,
        max_age=TOKEN_EXPIRY_DAYS * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=False,
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


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return user_doc_to_response(current_user)


@router.post("/logout", status_code=204)
async def logout(response: Response):
    # No auth required: the cookie must be cleared even when the token
    # is expired or invalid, otherwise the user can never sign out.
    response.delete_cookie(
        key=TOKEN_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=False,
    )
