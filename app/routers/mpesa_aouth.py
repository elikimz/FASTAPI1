import httpx
from fastapi import HTTPException
from ..config import setting

async def get_mpesa_token():
    url = f"{setting.MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    auth = (setting.MPESA_CONSUMER_KEY, setting.MPESA_CONSUMER_SECRET)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, auth=auth)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch M-Pesa token")
