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

from fastapi import FastAPI, HTTPException, status, Query
from fastapi.responses import PlainTextResponse

from constants import default_response, SUPPORTED_ATTACHMENT_TYPES
from schemas import GetUserResponseBody, GetUsersResponseBody, InstagramWebhookRequestPayload, GetAttachmentResponseBody, GetAttachmentsResponseBody
from models import Attachment, User

from db import database
attachment_collection = database["attachments"]
user_collection = database["users"]

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
    
    sender_id = messaging[0]["sender"]["id"]
    logger.info(f"Message received from sender ID: {sender_id}")
    
    # Check if the sender is a known user in the database
    user = user_collection.find_one({"id": sender_id})
    
    if user:
        logger.info(f"Known user detected. Sender ID: {sender_id}. Ignoring.")
    else:
        logger.info(f"New user detected. Storing sender ID: {sender_id} in the database.")
        user = User(id=sender_id)
        user_collection.insert_one(user.model_dump())
    
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

@app.get("/api/v1/users", response_model=GetUsersResponseBody, tags=["users"])
def get_users():
    try:
        users = list(user_collection.find())
        total_users = len(users)
        response_body = GetUsersResponseBody(
            users=[GetUserResponseBody(**user) for user in users],
            total=total_users
        )
        
        return response_body        
    except Exception as e:
        logger.exception(f"Failed to retrieve users from database: {e}")
        return HTTPException(
            detail="Failed to retrieve users.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
@app.get("/api/v1/attachments", response_model=GetAttachmentsResponseBody, tags=["attachments"])
def get_attachments(
    page_num: int = Query(1, ge=1), 
    page_size: int = Query(5, ge=1),
    # required parameter to filter attachments by type (...)
    type: str = Query(..., description="Filter attachments by type (e.g., 'image', 'video', 'audio')")
):
    skip = (page_num - 1) * page_size
    limit = page_size

    filter_query = {"type": type}
    
    try:
        attachments_cursor = (
            attachment_collection
            .find(filter_query)
            .sort("timestamp", -1)
            .skip(skip)
            .limit(limit)
        )
        
        attachments_list = list(attachments_cursor)

        total_attachments = attachment_collection.count_documents(filter_query)

        response_body = GetAttachmentsResponseBody(
            attachments=[GetAttachmentResponseBody(**attachment) for attachment in attachments_list],
            total=total_attachments
        )

        return response_body

    except Exception as e:
        logger.exception(f"Failed to retrieve attachments from database: {e}")
        return HTTPException(
            detail="Failed to retrieve attachments.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )