# app/main.py
from fastapi import FastAPI, Security
from fastapi.security import APIKeyHeader
from app.routes import claims, eligibility
from app.config import settings

app = FastAPI(
    title="EDI2Insights API",
    description="Ingest 837P claims and 270 eligibility EDI files",
    version="1.0.0",
)

# API key auth header
api_key_header = APIKeyHeader(name="X-API-Key")

app.include_router(claims.router, prefix="/claims", tags=["837P Claims"])
app.include_router(eligibility.router, prefix="/eligibility", tags=["270 Eligibility"])

@app.get("/health")
async def health():
    return {"status": "ok", "service": "EDI2Insights"}

# Run: uvicorn app.main:app --reload