# app/auth.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
import os

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_KEY", "test-key-123"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key