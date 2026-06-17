import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.parsers.edi_837p import parse_837p
from app.transformers.claims_transformer import store_claim
from app.kafka.producer import publish_event
from app.auth import verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = (".edi", ".txt", ".837")


@router.post("/ingest")
async def ingest_claim(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    if not file.filename.endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(400, detail=f"Invalid file type. Allowed: {ALLOWED_EXTENSIONS}")

    content = await file.read()
    try:
        raw_edi = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(400, detail="File must be UTF-8 encoded")

    parsed = parse_837p(raw_edi)

    # Persist to DuckDB warehouse
    store_claim(parsed)

    # Also stream to Kafka (best-effort — won't fail the request if Kafka is down)
    try:
        await publish_event(
            topic="edi-837p-claims",
            key=parsed["claim_id"],
            value={k: v for k, v in parsed.items() if k != "raw_segments"},
        )
    except Exception as exc:
        logger.warning("Kafka publish failed (non-fatal): %s", exc)

    return {
        "status":    "stored",
        "claim_id":  parsed["claim_id"],
        "segments":  parsed["segment_count"],
        "patient":   parsed.get("patient_name"),
        "amount":    parsed.get("claim_amount"),
    }


@router.get("/{claim_id}/status")
async def claim_status(claim_id: str, _: str = Depends(verify_api_key)):
    from app.warehouse.duckdb_client import get_connection
    conn = get_connection()
    row = conn.execute(
        "SELECT claim_id, claim_amount, ingested_at FROM claims WHERE claim_id = ?",
        [claim_id],
    ).fetchone()
    if not row:
        raise HTTPException(404, detail="Claim not found")
    return {"claim_id": row[0], "amount": row[1], "ingested_at": str(row[2]), "status": "stored"}
