import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.parsers.edi_270 import parse_270
from app.transformers.eligibility_transformer import store_inquiry
from app.kafka.producer import publish_event
from app.auth import verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest")
async def ingest_eligibility(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    content = await file.read()
    try:
        raw_edi = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(400, detail="File must be UTF-8 encoded")

    parsed = parse_270(raw_edi)

    # Persist to DuckDB warehouse
    store_inquiry(parsed)

    # Also stream to Kafka (best-effort)
    try:
        await publish_event(
            topic="edi-270-eligibility",
            key=parsed["inquiry_id"],
            value=parsed,
        )
    except Exception as exc:
        logger.warning("Kafka publish failed (non-fatal): %s", exc)

    return {
        "status":     "stored",
        "inquiry_id": parsed["inquiry_id"],
        "member":     f"{parsed.get('member_first_name', '')} {parsed.get('member_last_name', '')}".strip(),
        "payer":      parsed.get("payer_name"),
    }


@router.get("/{inquiry_id}/status")
async def inquiry_status(inquiry_id: str, _: str = Depends(verify_api_key)):
    from app.warehouse.duckdb_client import get_connection
    conn = get_connection()
    row = conn.execute(
        "SELECT inquiry_id, member_id, ingested_at FROM eligibility_inquiries WHERE inquiry_id = ?",
        [inquiry_id],
    ).fetchone()
    if not row:
        raise HTTPException(404, detail="Inquiry not found")
    return {"inquiry_id": row[0], "member_id": row[1], "ingested_at": str(row[2]), "status": "stored"}
