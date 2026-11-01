import os
import json
from dotenv import load_dotenv
load_dotenv()

import logging
logger = logging.getLogger(__name__)

from constants import INSTAGRAM_USER_FIELDS
from http_client import fetch

def fetch_instagram_user_info(user_id: str):
    url = f"{os.getenv('INSTAGRAM_API_HOST')}{os.getenv('INSTAGRAM_API_VERSION')}/{user_id}"
    params = {
        "fields": INSTAGRAM_USER_FIELDS,
        "access_token": os.getenv('ACCESS_TOKEN')
    }
    
    try:
        response_data = json.loads(fetch(url, params=params).decode("utf-8"))
        return response_data
    except Exception as e:
        logger.error(f"Error fetching Instagram user info: {e}")
        raise