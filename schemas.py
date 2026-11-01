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
    
class GetUserResponseBody(BaseModel):
    id: str
    
class GetUsersResponseBody(BaseModel):
    users: list[GetUserResponseBody]
    total: int
    
class GetInstagramUserResponseBody(BaseModel):
    name: str
    username: str
    profile_pic: str
    
class DownloadAttachmentResponseBody(BaseModel):
    base64_data: str
    mime_type: str
    extension: str