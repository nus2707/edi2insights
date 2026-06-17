import os
import duckdb
from app.config import settings

_conn: duckdb.DuckDBPyConnection | None = None


def get_connection() -> duckdb.DuckDBPyConnection:
    global _conn
    if _conn is None:
        os.makedirs(os.path.dirname(settings.duckdb_path), exist_ok=True)
        _conn = duckdb.connect(settings.duckdb_path)
        _init_schema(_conn)
    return _conn


def _init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            claim_id         VARCHAR PRIMARY KEY,
            ingested_at      TIMESTAMP,
            sender_id        VARCHAR,
            receiver_id      VARCHAR,
            patient_name     VARCHAR,
            claim_amount     DOUBLE,
            service_date     DATE,
            diagnosis_codes  VARCHAR[],
            procedure_codes  VARCHAR[],
            segment_count    INTEGER,
            raw_json         JSON,
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS eligibility_inquiries (
            inquiry_id        VARCHAR PRIMARY KEY,
            ingested_at       TIMESTAMP,
            transaction_date  DATE,
            reference_id      VARCHAR,
            sender_id         VARCHAR,
            receiver_id       VARCHAR,
            payer_name        VARCHAR,
            payer_id          VARCHAR,
            provider_npi      VARCHAR,
            provider_name     VARCHAR,
            member_id         VARCHAR,
            member_last_name  VARCHAR,
            member_first_name VARCHAR,
            member_dob        DATE,
            member_gender     VARCHAR,
            service_types     JSON,
            segment_count     INTEGER,
            raw_json          JSON,
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
