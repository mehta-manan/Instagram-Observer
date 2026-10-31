from pydantic import BaseModel
from typing import Any

class InstagramWebhookRequestPayload(BaseModel):
    object: str
    entry: list[dict[str, Any]]
    
class GetAttachmentResponseBody(BaseModel):
    mid: str
    timestamp: str
    sender_id: str
    type: str
    url: str
    
class GetAttachmentsResponseBody(BaseModel):
    attachments: list[GetAttachmentResponseBody]
    total: int