import json
from datetime import datetime
from app.warehouse.duckdb_client import get_connection


def store_inquiry(parsed: dict) -> None:
    """Upsert a parsed 270 eligibility inquiry into DuckDB."""
    conn = get_connection()

    ingested_at = _parse_ts(parsed.get("ingested_at"))
    transaction_date = _parse_date(parsed.get("transaction_date"))
    member_dob = _parse_date(parsed.get("member_dob"))

    conn.execute("""
        INSERT OR REPLACE INTO eligibility_inquiries (
            inquiry_id, ingested_at, transaction_date, reference_id,
            sender_id, receiver_id, payer_name, payer_id,
            provider_npi, provider_name, member_id, member_last_name,
            member_first_name, member_dob, member_gender, service_types,
            segment_count, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        parsed.get("inquiry_id"),
        ingested_at,
        transaction_date,
        parsed.get("reference_id"),
        parsed.get("sender_id"),
        parsed.get("receiver_id"),
        parsed.get("payer_name"),
        parsed.get("payer_id"),
        parsed.get("provider_npi"),
        parsed.get("provider_name"),
        parsed.get("member_id"),
        parsed.get("member_last_name"),
        parsed.get("member_first_name"),
        member_dob,
        parsed.get("member_gender"),
        json.dumps(parsed.get("service_types", [])),
        parsed.get("segment_count"),
        json.dumps(parsed),
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
