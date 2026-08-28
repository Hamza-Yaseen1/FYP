from typing import List, Optional

from pydantic import BaseModel, Field


class MetaText(BaseModel):
    body: Optional[str] = None


class MetaMessage(BaseModel):
    from_: str = Field(alias="from")
    id: str
    timestamp: str
    type: str
    text: Optional[MetaText] = None


class MetaContactProfile(BaseModel):
    name: Optional[str] = None


class MetaContact(BaseModel):
    wa_id: str
    profile: Optional[MetaContactProfile] = None


class MetaMetadata(BaseModel):
    display_phone_number: Optional[str] = None
    phone_number_id: Optional[str] = None


class MetaValue(BaseModel):
    messaging_product: Optional[str] = None
    metadata: Optional[MetaMetadata] = None
    contacts: Optional[List[MetaContact]] = None
    messages: Optional[List[MetaMessage]] = None


class MetaChange(BaseModel):
    value: MetaValue
    field: str = ""


class MetaEntry(BaseModel):
    id: Optional[str] = None
    changes: List[MetaChange]


class MetaWebhookPayload(BaseModel):
    object: Optional[str] = None
    entry: Optional[List[MetaEntry]] = None