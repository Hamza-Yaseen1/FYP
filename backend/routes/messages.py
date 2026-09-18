from datetime import datetime, timezone
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from typing import Optional

from database import messages_collection
from dependencies import get_current_user
from models.message import (
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    message_doc_to_response,
)
from services.ai import process_message
from services.threads import resolve_and_stamp

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=MessageResponse, status_code=201)
async def create_message(
    payload: MessageCreate, current_user: dict = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    uid = str(current_user["_id"])

    _id = ObjectId()
    thread_id, conversation_id = None, None
    try:
        thread_id, conversation_id = await resolve_and_stamp(
            uid, payload.source, payload.sender, now
        )
    except Exception as exc:
        logger.warning(
            "Thread resolution failed for POST /messages; stored standalone: %s",
            exc,
            exc_info=True,
        )

    doc = {
        **payload.model_dump(),
        "_id": _id,
        "messageId": str(_id),
        "user_id": uid,
        "state": "active",
        "created_at": now,
        "updated_at": now,
        "received_at": now,
    }
    if thread_id:
        doc["threadId"] = thread_id
        doc["conversationId"] = conversation_id

    result = await messages_collection.insert_one(doc)

    ai_analysis = await process_message(
        payload.content,
        message_id=str(result.inserted_id),
        user_id=uid,
        thread_id=thread_id,
    )
    await messages_collection.update_one(
        {"_id": result.inserted_id},
        {"$set": {"ai_analysis": ai_analysis}},
    )
    doc["ai_analysis"] = ai_analysis

    return message_doc_to_response(doc)


@router.get("")
async def get_messages(
    current_user: dict = Depends(get_current_user),
    tab: Optional[str] = Query(None, description="Filter by tab: all, urgent, important, normal, unread"),
    source: Optional[str] = Query(None, description="Filter by source"),
    priority: Optional[str] = Query(None, description="Filter by priority: urgent, important, normal, low"),
    start_date: Optional[str] = Query(None, description="Filter messages from this date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter messages up to this date (ISO format)"),
    sender: Optional[str] = Query(None, description="Filter by sender"),
    search: Optional[str] = Query(None, description="Search across sender, content, and summary"),
    limit: int = Query(100, ge=1, le=200, description="Maximum messages to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    uid = str(current_user["_id"])
    query = {"user_id": uid}

    # Tab filter
    if tab and tab != "all":
        if tab == "unread":
            query["status"] = "unread"
        elif tab in ["urgent", "important", "normal"]:
            query["ai_analysis.priority"] = tab

    # Source filter
    if source:
        query["source"] = source

    # Priority filter
    if priority:
        query["ai_analysis.priority"] = priority

    # Date range filter
    if start_date or end_date:
        created_at_filter = {}
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                created_at_filter["$gte"] = start_dt
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                created_at_filter["$lte"] = end_dt
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        if "$gte" in created_at_filter and "$lte" in created_at_filter:
            if created_at_filter["$gte"] > created_at_filter["$lte"]:
                raise HTTPException(status_code=400, detail="Invalid date range: start_date must be before end_date")
        query["created_at"] = created_at_filter

    # Sender filter
    if sender:
        query["sender"] = sender

    # Search filter - use regex for flexible partial matching
    if search:
        # Use case-insensitive regex for better user experience
        # This allows partial matches in sender, content, and summary
        query["$or"] = [
            {"sender": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}},
            {"ai_analysis.summary": {"$regex": search, "$options": "i"}},
        ]

    # Get total count
    total = await messages_collection.count_documents(query)

    # Get messages with pagination
    cursor = messages_collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
    docs = await cursor.to_list(length=limit)

    return {
        "messages": [message_doc_to_response(doc) for doc in docs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/counts")
async def get_filter_counts(current_user: dict = Depends(get_current_user)):
    uid = str(current_user["_id"])
    base_query = {"user_id": uid}

    # Get tab counts
    all_count = await messages_collection.count_documents(base_query)
    urgent_count = await messages_collection.count_documents({**base_query, "ai_analysis.priority": "urgent"})
    important_count = await messages_collection.count_documents({**base_query, "ai_analysis.priority": "important"})
    normal_count = await messages_collection.count_documents({**base_query, "ai_analysis.priority": "normal"})
    unread_count = await messages_collection.count_documents({**base_query, "status": "unread"})

    # Get source counts
    source_pipeline = [
        {"$match": base_query},
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
    ]
    source_results = await messages_collection.aggregate(source_pipeline).to_list(length=100)
    sources = {r["_id"]: r["count"] for r in source_results if r["_id"]}

    # Get priority counts
    priority_pipeline = [
        {"$match": base_query},
        {"$group": {"_id": "$ai_analysis.priority", "count": {"$sum": 1}}},
    ]
    priority_results = await messages_collection.aggregate(priority_pipeline).to_list(length=100)
    priorities = {r["_id"]: r["count"] for r in priority_results if r["_id"]}

    return {
        "tabs": {
            "all": all_count,
            "urgent": urgent_count,
            "important": important_count,
            "normal": normal_count,
            "unread": unread_count,
        },
        "sources": sources,
        "priorities": priorities,
    }


@router.get("/senders")
async def get_unique_senders(current_user: dict = Depends(get_current_user)):
    uid = str(current_user["_id"])
    pipeline = [
        {"$match": {"user_id": uid}},
        {"$group": {"_id": "$sender", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    results = await messages_collection.aggregate(pipeline).to_list(length=100)
    senders = [{"name": r["_id"], "count": r["count"]} for r in results if r["_id"]]
    return {"senders": senders}


@router.get("/sources")
async def get_unique_sources(current_user: dict = Depends(get_current_user)):
    uid = str(current_user["_id"])
    pipeline = [
        {"$match": {"user_id": uid}},
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    results = await messages_collection.aggregate(pipeline).to_list(length=100)
    sources = [{"name": r["_id"], "count": r["count"]} for r in results if r["_id"]]
    return {"sources": sources}


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
