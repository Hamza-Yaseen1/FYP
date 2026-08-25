from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from database import messages_collection
from dependencies import get_current_user
from models.message import (
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    message_doc_to_response,
)
from services.ai import analyze_message

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=MessageResponse, status_code=201)
async def create_message(
    payload: MessageCreate, current_user: dict = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    doc = {
        **payload.model_dump(),
        "user_id": str(current_user["_id"]),
        "state": "active",
        "created_at": now,
        "updated_at": now,
    }
    result = await messages_collection.insert_one(doc)
    doc["_id"] = result.inserted_id

    ai_analysis = await analyze_message(payload.content, message_id=str(result.inserted_id))
    await messages_collection.update_one(
        {"_id": result.inserted_id},
        {"$set": {"ai_analysis": ai_analysis}},
    )
    doc["ai_analysis"] = ai_analysis

    return message_doc_to_response(doc)


@router.get("", response_model=list[MessageResponse])
async def get_messages(current_user: dict = Depends(get_current_user)):
    uid = str(current_user["_id"])
    cursor = messages_collection.find({"user_id": uid}).sort("created_at", -1)
    docs = await cursor.to_list(length=100)
    return [message_doc_to_response(doc) for doc in docs]


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str, current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=404)

    uid = str(current_user["_id"])
    doc = await messages_collection.find_one(
        {"_id": ObjectId(message_id), "user_id": uid}
    )
    if not doc:
        raise HTTPException(status_code=404)

    return message_doc_to_response(doc)


@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: str,
    payload: MessageUpdate,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=404)

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates["updated_at"] = datetime.now(timezone.utc)

    uid = str(current_user["_id"])
    result = await messages_collection.find_one_and_update(
        {"_id": ObjectId(message_id), "user_id": uid},
        {"$set": updates},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404)

    return message_doc_to_response(result)


@router.delete("/{message_id}", status_code=204)
async def delete_message(
    message_id: str, current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=404)

    uid = str(current_user["_id"])
    result = await messages_collection.delete_one(
        {"_id": ObjectId(message_id), "user_id": uid}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404)


VALID_PRIORITIES = ["urgent", "important", "normal", "low"]


@router.put("/{message_id}/priority", response_model=MessageResponse)
async def override_priority(
    message_id: str,
    priority: str,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=404)

    if priority not in VALID_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority. Must be one of: {VALID_PRIORITIES}",
        )

    now = datetime.now(timezone.utc)
    uid = str(current_user["_id"])
    result = await messages_collection.find_one_and_update(
        {"_id": ObjectId(message_id), "user_id": uid},
        {
            "$set": {
                "ai_analysis.priority": priority,
                "ai_analysis.confidence": 1.0,
                "ai_analysis.explanation": "User override",
                "updated_at": now,
            }
        },
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404)

    return message_doc_to_response(result)
