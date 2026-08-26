from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class ExtractedTask(BaseModel):
    description: str
    deadline: Optional[str] = None
    priority_indicator: Optional[str] = None
    requires_action: bool = True


class TaskResponse(BaseModel):
    id: str
    description: str
    deadline: Optional[str] = None
    priority_indicator: Optional[str] = None
    requires_action: bool = True
    status: str = "pending"
    source_message_id: str
    source_message_preview: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None
