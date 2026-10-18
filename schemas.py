from pydantic import BaseModel
from typing import Any

class InstagramWebhookRequestPayload(BaseModel):
    object: str
    entry: list[dict[str, Any]]