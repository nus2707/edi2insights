# app/routes/claims.py  — 837P Professional Claims
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.parsers.edi_837p import parse_837p
from app.kafka.producer import publish_event
from app.auth import verify_api_key

router = APIRouter()

@router.post("/ingest")
async def ingest_claim(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    if not file.filename.endswith((".edi", ".txt", ".837")):
        raise HTTPException(400, detail="Invalid file type")

    content = await file.read()
    raw_edi = content.decode("utf-8")

    # Parse EDI → structured dict
    parsed = parse_837p(raw_edi)

    # Stream to Kafka topic
    await publish_event(
        topic="edi-837p-claims",
        key=parsed["claim_id"],
        value=parsed,
    )

    return {
        "status": "queued",
        "claim_id": parsed["claim_id"],
        "segments": parsed["segment_count"],
    }

@router.get("/{claim_id}/status")
async def claim_status(claim_id: str):
    return {"claim_id": claim_id, "status": "processing"}