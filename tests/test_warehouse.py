import pytest
import duckdb
from unittest.mock import patch
from app.parsers.edi_837p import parse_837p
from app.parsers.edi_270 import parse_270

SAMPLE_837P = (
    "ISA*00*          *00*          *ZZ*CLINIC001      *ZZ*PAYER999       "
    "*240601*1032*^*00501*000000001*0*P*:~"
    "NM1*QC*1*SMITH*JANE****MI*MEM999~"
    "CLM*CLAIM-002*500.00***11:B:1*Y*A*Y*I~"
    "HI*ABK:Z001~"
    "SV1*HC:99214*200.00*UN*1***1~"
    "SE*5*0001~"
)

SAMPLE_270 = (
    "ISA*00*          *00*          *ZZ*CLINIC001      *ZZ*PAYER999       "
    "*240601*1032*^*00501*000000001*0*P*:~"
    "BHT*0022*13*10001234*20240601*1032~"
    "NM1*PR*2*AETNA*****PI*PAYER111~"
    "NM1*IL*1*SMITH*JANE****MI*MEM999~"
    "DMG*D8*19900101*F~"
    "EQ*1~"
    "SE*6*0001~"
)


@pytest.fixture
def in_memory_db():
    """Patch get_connection to return an isolated in-memory DuckDB."""
    conn = duckdb.connect(":memory:")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            claim_id VARCHAR PRIMARY KEY, ingested_at TIMESTAMP,
            sender_id VARCHAR, receiver_id VARCHAR, patient_name VARCHAR,
            claim_amount DOUBLE, service_date DATE,
            diagnosis_codes VARCHAR[], procedure_codes VARCHAR[],
            segment_count INTEGER, raw_json JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS eligibility_inquiries (
            inquiry_id VARCHAR PRIMARY KEY, ingested_at TIMESTAMP,
            transaction_date DATE, reference_id VARCHAR,
            sender_id VARCHAR, receiver_id VARCHAR,
            payer_name VARCHAR, payer_id VARCHAR,
            provider_npi VARCHAR, provider_name VARCHAR,
            member_id VARCHAR, member_last_name VARCHAR, member_first_name VARCHAR,
            member_dob DATE, member_gender VARCHAR,
            service_types JSON, segment_count INTEGER, raw_json JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    with patch("app.transformers.claims_transformer.get_connection", return_value=conn), \
         patch("app.transformers.eligibility_transformer.get_connection", return_value=conn):
        yield conn


def test_store_claim(in_memory_db):
    from app.transformers.claims_transformer import store_claim
    parsed = parse_837p(SAMPLE_837P)
    store_claim(parsed)
    count = in_memory_db.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    assert count == 1


def test_claim_amount_stored(in_memory_db):
    from app.transformers.claims_transformer import store_claim
    parsed = parse_837p(SAMPLE_837P)
    store_claim(parsed)
    row = in_memory_db.execute("SELECT claim_amount FROM claims").fetchone()
    assert row[0] == 500.00


def test_store_inquiry(in_memory_db):
    from app.transformers.eligibility_transformer import store_inquiry
    parsed = parse_270(SAMPLE_270)
    store_inquiry(parsed)
    count = in_memory_db.execute("SELECT COUNT(*) FROM eligibility_inquiries").fetchone()[0]
    assert count == 1


def test_inquiry_member_stored(in_memory_db):
    from app.transformers.eligibility_transformer import store_inquiry
    parsed = parse_270(SAMPLE_270)
    store_inquiry(parsed)
    row = in_memory_db.execute(
        "SELECT member_last_name, member_first_name FROM eligibility_inquiries"
    ).fetchone()
    assert row[0] == "SMITH"
    assert row[1] == "JANE"
