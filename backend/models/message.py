from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from models.task import ExtractedTask


class AIAnalysis(BaseModel):
    priority: str = "pending"
    confidence: float = 0.0
    explanation: Optional[str] = None
    summary: Optional[str] = None
    recommended_action: str = ""
    recommended_actions: list[str] = []
    tasks_extracted: list[ExtractedTask] = []
    deadlines: list[str] = []
    needs_attention: bool = False
    attention_reason: str = ""
    provider: str = "unknown"
    analyzed_at: Optional[datetime] = None
    status: str = "pending"


class MessageCreate(BaseModel):
    sender: str
    content: str
    source: str
    status: str = "unread"


class MessageUpdate(BaseModel):
    sender: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    state: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    sender: str
    content: str
    source: str
    status: str
    state: str
    ai_analysis: Optional[AIAnalysis] = None
    created_at: datetime
    updated_at: datetime


def message_doc_to_response(doc: dict) -> dict:
    ai_analysis = doc.get("ai_analysis")
    if ai_analysis:
        ai_analysis = AIAnalysis(**ai_analysis)

    return {
        "id": str(doc["_id"]),
        "sender": doc["sender"],
        "content": doc["content"],
        "source": doc["source"],
        "status": doc["status"],
        "state": doc.get("state", "active"),
        "ai_analysis": ai_analysis,
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }
