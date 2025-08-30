from fastapi import APIRouter, HTTPException
from fastapi_cache.decorator import cache
from ..config import settings

router = APIRouter()

@router.get("/api/config", tags=["Configuration"])
@cache()
async def get_app_config():
    api_key = settings.MAPS_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=500, detail="Server configuration error: Maps API Key not set."
        )
    return {"googleMapsApiKey": api_key}