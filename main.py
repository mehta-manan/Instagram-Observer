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
# MongoDB driver → WARNING
logging.getLogger("pymongo").setLevel(logging.WARNING)

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, status, Query
from fastapi.responses import PlainTextResponse

from constants import default_response, SUPPORTED_ATTACHMENT_TYPES
from schemas import InstagramWebhookRequestPayload
from models import Attachment

from db import database
attachment_collection = database["attachments"]

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
    messaging = entry.get("messaging", [])
    message = entry["messaging"][0].get("message", {})
    
    logger.debug(f"Entry received: {entry}")
    
    if message.get("is_echo"):
        logger.info("Echo message received. Ignoring.")
        return default_response
    
    if not message.get("attachments"):
        logger.info("No-attachment message received. Ignoring.")
        return default_response
    
    attachments = message["attachments"]
    
    for attachment in attachments:
        attachment_type = attachment.get("type")
        logger.info(f"Attachment type received: {attachment_type}")
        
        if attachment_type in SUPPORTED_ATTACHMENT_TYPES:
            logger.info(f"Processing attachment of type: {attachment_type}")
            
            # mongodb stores bson date internally as UTC, even if timezone is specified.
            india_time = datetime.fromtimestamp(
                messaging[0]["timestamp"] / 1000,
                tz=ZoneInfo("Asia/Kolkata")
                )
            
            # so we convert the time to string before storing it
            india_timestamp_str = india_time.strftime("%Y-%m-%d %H:%M:%S")
             
            attachment = Attachment(
                mid=messaging[0]["message"]["mid"],
                timestamp=india_timestamp_str,
                sender_id=messaging[0]["sender"]["id"],
                type=attachment["type"],
                url=attachment.get("payload", {}).get("url"),
            )

            try:
                logger.info(f"Storing attachment in database: {attachment}")

                attachment_collection.insert_one(
                    attachment.model_dump(mode="python")
                )

                logger.info("Attachment stored successfully")

            except Exception as e:
                logger.exception(f"Failed to store attachment in database: {e}")
        else:
            logger.warning(f"Unsupported attachment type received: {attachment_type}")
        
    return default_response