# app/routes/eligibility.py  — 270 Eligibility Inquiries
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.parsers.edi_270 import parse_270
from app.kafka.producer import publish_event
from app.auth import verify_api_key

router = APIRouter()

@router.post("/ingest")
async def ingest_eligibility(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    content = await file.read()
    raw_edi = content.decode("utf-8")

    parsed = parse_270(raw_edi)

    await publish_event(
        topic="edi-270-eligibility",
        key=parsed["inquiry_id"],
        value=parsed,
    )

    return {"status": "queued", "inquiry_id": parsed["inquiry_id"]}