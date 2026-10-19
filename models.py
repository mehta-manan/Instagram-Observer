
from pydantic import BaseModel
from typing import Optional

class Attachment(BaseModel):
    mid: str
    timestamp: str
    sender_id: str
    type: str
    url: Optional[str] = None
