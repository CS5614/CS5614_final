import os
from fastapi import APIRouter, HTTPException
from fastapi_cache.decorator import cache
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()


@lru_cache()  # Optional: cache the key lookup
def get_api_key():
    key = os.getenv("Maps_API_KEY")
    return key


@router.get("/api/config", tags=["Configuration"])
@cache()
async def get_app_config():
    api_key = get_api_key()
    if not api_key:
        raise HTTPException(
            status_code=500, detail="Server configuration error: Maps API Key not set."
        )
    return {"googleMapsApiKey": api_key}
