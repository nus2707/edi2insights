from app.warehouse.duckdb_client import get_connection


def claims_summary() -> dict:
    conn = get_connection()
    row = conn.execute("""
        SELECT
            COUNT(*)                        AS total_claims,
            COALESCE(SUM(claim_amount), 0)  AS total_amount,
            COALESCE(AVG(claim_amount), 0)  AS avg_amount,
            COALESCE(MAX(claim_amount), 0)  AS max_amount,
            COALESCE(MIN(claim_amount), 0)  AS min_amount
        FROM claims
    """).fetchone()
    return {
        "total_claims": row[0],
        "total_amount": round(row[1], 2),
        "avg_amount":   round(row[2], 2),
        "max_amount":   round(row[3], 2),
        "min_amount":   round(row[4], 2),
    }


def top_diagnosis_codes(limit: int = 10) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(f"""
        SELECT code, COUNT(*) AS frequency
        FROM (
            SELECT UNNEST(diagnosis_codes) AS code FROM claims
        )
        GROUP BY code
        ORDER BY frequency DESC
        LIMIT {limit}
    """).fetchall()
    return [{"code": r[0], "frequency": r[1]} for r in rows]


def top_procedure_codes(limit: int = 10) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(f"""
        SELECT code, COUNT(*) AS frequency
        FROM (
            SELECT UNNEST(procedure_codes) AS code FROM claims
        )
        GROUP BY code
        ORDER BY frequency DESC
        LIMIT {limit}
    """).fetchall()
    return [{"code": r[0], "frequency": r[1]} for r in rows]


def claims_by_sender() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT sender_id, COUNT(*) AS claim_count, SUM(claim_amount) AS total_amount
        FROM claims
        GROUP BY sender_id
        ORDER BY claim_count DESC
    """).fetchall()
    return [{"sender_id": r[0], "claim_count": r[1], "total_amount": round(r[2] or 0, 2)} for r in rows]


def eligibility_summary() -> dict:
    conn = get_connection()
    row = conn.execute("""
        SELECT
            COUNT(*)                                 AS total_inquiries,
            COUNT(DISTINCT member_id)                AS unique_members,
            COUNT(DISTINCT provider_npi)             AS unique_providers,
            COUNT(DISTINCT payer_id)                 AS unique_payers
        FROM eligibility_inquiries
    """).fetchone()
    return {
        "total_inquiries":  row[0],
        "unique_members":   row[1],
        "unique_providers": row[2],
        "unique_payers":    row[3],
    }


def recent_claims(limit: int = 20) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(f"""
        SELECT claim_id, sender_id, receiver_id, patient_name,
               claim_amount, service_date, diagnosis_codes, procedure_codes, ingested_at
        FROM claims
        ORDER BY ingested_at DESC
        LIMIT {limit}
    """).fetchall()
    cols = ["claim_id", "sender_id", "receiver_id", "patient_name",
            "claim_amount", "service_date", "diagnosis_codes", "procedure_codes", "ingested_at"]
    return [dict(zip(cols, r)) for r in rows]


def recent_inquiries(limit: int = 20) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(f"""
        SELECT inquiry_id, member_id, member_last_name, member_first_name,
               payer_name, provider_name, transaction_date, ingested_at
        FROM eligibility_inquiries
        ORDER BY ingested_at DESC
        LIMIT {limit}
    """).fetchall()
    cols = ["inquiry_id", "member_id", "member_last_name", "member_first_name",
            "payer_name", "provider_name", "transaction_date", "ingested_at"]
    return [dict(zip(cols, r)) for r in rows]
