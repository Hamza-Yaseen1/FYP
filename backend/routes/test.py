"""
TEMPORARY LOAD TESTING ROUTE
This module is for testing/development only and should be removed before production.
"""

import asyncio
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from pydantic import BaseModel, Field

from database import messages_collection
from dependencies import get_current_user
from services.ai import process_message
from services.threads import resolve_and_stamp

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["test"])


class BulkMessageRequest(BaseModel):
    count: int = Field(..., ge=1, le=150, description="Number of messages to create (max 150)")


# Sample realistic messages for load testing
SAMPLE_MESSAGES = [
    {
        "sender": "Boss",
        "content": "Can you prepare the Q4 report by end of day? It's urgent.",
        "source": "email"
    },
    {
        "sender": "Team Lead",
        "content": "Meeting rescheduled to 3pm tomorrow. Please confirm attendance.",
        "source": "slack"
    },
    {
        "sender": "Client Services",
        "content": "Client is requesting an update on the project timeline.",
        "source": "email"
    },
    {
        "sender": "HR Department",
        "content": "Reminder: Submit your timesheet by Friday.",
        "source": "email"
    },
    {
        "sender": "Marketing Team",
        "content": "New campaign materials are ready for review. Let me know your thoughts.",
        "source": "slack"
    },
    {
        "sender": "Tech Support",
        "content": "Your ticket #1234 has been resolved. Please verify the fix.",
        "source": "email"
    },
    {
        "sender": "Project Manager",
        "content": "Sprint planning meeting tomorrow at 10am. Be prepared to discuss blockers.",
        "source": "slack"
    },
    {
        "sender": "Finance",
        "content": "Invoice #5678 is pending approval. Please review and approve.",
        "source": "email"
    },
    {
        "sender": "Developer",
        "content": "Code review needed for PR #234. Should be quick to review.",
        "source": "github"
    },
    {
        "sender": "Customer",
        "content": "Thanks for the quick response! Everything is working now.",
        "source": "whatsapp"
    },
    {
        "sender": "Vendor",
        "content": "Shipment delayed due to weather. New ETA is next Monday.",
        "source": "email"
    },
    {
        "sender": "Sales Team",
        "content": "Great news! We just closed the deal with ABC Corp.",
        "source": "slack"
    },
    {
        "sender": "Security",
        "content": "Password reset requested for your account. Click here to confirm.",
        "source": "email"
    },
    {
        "sender": "Designer",
        "content": "New mockups are ready. Check them out in Figma.",
        "source": "slack"
    },
    {
        "sender": "Operations",
        "content": "Server maintenance scheduled for Saturday 2am-4am EST.",
        "source": "email"
    },
]


@router.post("/bulk-messages")
async def create_bulk_messages(
    payload: BulkMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    TEMPORARY ENDPOINT FOR LOAD TESTING
    Creates multiple simulated messages for the current user.
    Each message goes through the full AI analysis pipeline.
    """
    uid = str(current_user["_id"])
    count = payload.count
    
    logger.info(f"Starting bulk message creation: {count} messages for user {uid}")
    
    created_ids = []
    errors = []
    
    for i in range(count):
        try:
            # Small delay to prevent overwhelming the server
            if i > 0 and i % 10 == 0:
                await asyncio.sleep(0.5)
            
            # Cycle through sample messages
            sample = SAMPLE_MESSAGES[i % len(SAMPLE_MESSAGES)]
            
            # Generate unique content by adding timestamp
            now = datetime.now(timezone.utc)
            content = f"{sample['content']} [Test #{i+1} at {now.strftime('%H:%M:%S')}]"
            
            # Create message document
            _id = ObjectId()
            thread_id, conversation_id = None, None
            
            try:
                thread_id, conversation_id = await resolve_and_stamp(
                    uid, sample['source'], sample['sender'], now
                )
            except Exception as exc:
                logger.warning(f"Thread resolution failed for bulk message {i}: {exc}")
            
            doc = {
                "_id": _id,
                "messageId": str(_id),
                "user_id": uid,
                "sender": sample['sender'],
                "content": content,
                "source": sample['source'],
                "state": "active",
                "status": "unread",
                "created_at": now,
                "updated_at": now,
                "received_at": now,
            }
            
            if thread_id:
                doc["threadId"] = thread_id
                doc["conversationId"] = conversation_id
            
            # Insert message
            result = await messages_collection.insert_one(doc)
            
            # Run AI analysis
            ai_analysis = await process_message(
                content,
                message_id=str(result.inserted_id),
                user_id=uid,
                thread_id=thread_id,
            )
            
            # Update with AI analysis
            await messages_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"ai_analysis": ai_analysis}},
            )
            
            created_ids.append(str(result.inserted_id))
            
            # Log progress every 20 messages
            if (i + 1) % 20 == 0:
                logger.info(f"Bulk creation progress: {i+1}/{count} messages created")
        
        except Exception as exc:
            logger.error(f"Failed to create bulk message {i}: {exc}")
            errors.append(f"Message {i+1}: {str(exc)}")
    
    logger.info(f"Bulk message creation complete: {len(created_ids)}/{count} successful")
    
    return {
        "success": True,
        "created": len(created_ids),
        "requested": count,
        "message_ids": created_ids[:10],  # Return first 10 IDs only
        "errors": errors[:5] if errors else [],  # Return first 5 errors only
    }
