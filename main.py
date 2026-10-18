import os
from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M"
)
logger = logging.getLogger(__name__)
# Your app → DEBUG
logger.setLevel(logging.DEBUG)

from fastapi import FastAPI, status, Query
from fastapi.responses import PlainTextResponse

from pydantic import BaseModel
from typing import Any

class InstagramWebhookRequestPayload(BaseModel):
    object: str
    entry: list[dict[str, Any]]

default_response = {
    "status": "ok"
}

app = FastAPI()

@app.get('/')
def root():
    return "Hello from Instagram Observer server."

@app.get('/webhook/instagram', response_class=PlainTextResponse)
def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    if hub_mode == "subscribe" and hub_verify_token == os.getenv('WEBHOOK_VERIFY_TOKEN'):
        return hub_challenge
    
    return PlainTextResponse(
        "Verification failed.",
        status_code=status.HTTP_403_FORBIDDEN
    )
    
@app.post("/webhook/instagram")
def instagram_webhook(
    payload: InstagramWebhookRequestPayload
):     
    entry = payload.entry[0]
    message = entry["messaging"][0].get("message", {})
    
    if message.get("is_echo"):
        logger.info("Echo message received. Ignoring.")
        return default_response
    
    if not message.get("attachments"):
        logger.info("No-attachment message received. Ignoring.")
        return default_response
    
    attachments = message["attachments"]
    
    for attachment in attachments:
        attachment_type = attachment.get("type")
        
        if attachment_type == "ephemeral":
            logger.info("Ephemeral message received.")
        elif attachment_type == "image" or attachment_type == "video" or attachment_type == "audio":
            logger.info("Media message received.")
        else:
            logger.warning(f"Unsupported type received: {attachment_type}")
    
    return default_response