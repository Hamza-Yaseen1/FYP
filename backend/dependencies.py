from bson import ObjectId
from fastapi import HTTPException, Request

from database import users_collection
from services.security import TOKEN_COOKIE_NAME, decode_token


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get(TOKEN_COOKIE_NAME)
    user_id = decode_token(token) if token else None

    if not user_id or not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=401, detail="Not authenticated.")

    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    return user
