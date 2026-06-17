import json
from datetime import datetime
from app.warehouse.duckdb_client import get_connection


def store_claim(parsed: dict) -> None:
    """Upsert a parsed 837P claim into DuckDB."""
    conn = get_connection()

    ingested_at = _parse_ts(parsed.get("ingested_at"))
    service_date = _parse_date(parsed.get("service_date"))

    conn.execute("""
        INSERT OR REPLACE INTO claims (
            claim_id, ingested_at, sender_id, receiver_id, patient_name,
            claim_amount, service_date, diagnosis_codes, procedure_codes,
            segment_count, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        parsed.get("claim_id"),
        ingested_at,
        parsed.get("sender_id"),
        parsed.get("receiver_id"),
        parsed.get("patient_name"),
        parsed.get("claim_amount"),
        service_date,
        parsed.get("diagnosis_codes", []),
        parsed.get("procedure_codes", []),
        parsed.get("segment_count"),
        json.dumps({k: v for k, v in parsed.items() if k != "raw_segments"}),
    ])


def _parse_ts(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _parse_date(value):
    if not value:
        return None
    try:
        from datetime import date
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None
