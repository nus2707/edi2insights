# EDI2Insights

End-to-end healthcare EDI data pipeline — ingest X12 **837P** (professional claims) and **270** (eligibility inquiries) files, stream through **Apache Kafka**, persist to **DuckDB**, and query via a **FastAPI** analytics layer.

No cloud account required. Everything runs locally with open-source tools.

---

## Architecture

```
EDI Files (.edi)
       │
       ▼
┌─────────────────┐
│  FastAPI API    │  POST /claims/ingest
│  (ingest layer) │  POST /eligibility/ingest
└────────┬────────┘
         │  parse (X12 segments)
         ▼
┌─────────────────┐        ┌──────────────────┐
│  EDI Parsers    │        │  Apache Kafka     │
│  837P / 270     │──────▶ │  (async stream)   │
└────────┬────────┘        └────────┬─────────┘
         │                          │
         │ (synchronous)            │ (consumer)
         ▼                          ▼
┌─────────────────────────────────────────────┐
│               DuckDB Warehouse              │
│   tables: claims, eligibility_inquiries     │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Analytics API  │  GET /analytics/claims/summary
│  (read layer)   │  GET /analytics/eligibility/summary
└─────────────────┘
```

### Component roles

| Component | Role |
|-----------|------|
| **FastAPI** | REST API — accepts EDI file uploads, returns structured JSON |
| **EDI Parsers** | Pure-Python X12 segment parsers for 837P and 270 |
| **Transformers** | Convert parsed dicts to strongly-typed DuckDB rows |
| **DuckDB** | Embedded OLAP warehouse (replaces BigQuery / Redshift) — zero config, file-based |
| **Kafka** | Optional async streaming (best-effort; API works without Kafka) |
| **Analytics API** | Query layer — summaries, top codes, recent records |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API

```bash
uvicorn app.main:app --reload
```

API is live at **http://localhost:8000**
Swagger docs at **http://localhost:8000/docs**

### 3. Ingest sample EDI files

**Via CLI (no server needed):**

```bash
python ingest_cli.py tests/sample_837p.edi tests/sample_270.edi
```

**Via API:**

```bash
# Ingest an 837P claim
curl -X POST http://localhost:8000/claims/ingest \
  -H "X-API-Key: test-key-123" \
  -F "file=@tests/sample_837p.edi"

# Ingest a 270 eligibility inquiry
curl -X POST http://localhost:8000/eligibility/ingest \
  -H "X-API-Key: test-key-123" \
  -F "file=@tests/sample_270.edi"
```

### 4. Query analytics

```bash
# Claims summary (totals, averages)
curl http://localhost:8000/analytics/claims/summary \
  -H "X-API-Key: test-key-123"

# Top diagnosis codes
curl http://localhost:8000/analytics/claims/top-diagnosis \
  -H "X-API-Key: test-key-123"

# Eligibility summary
curl http://localhost:8000/analytics/eligibility/summary \
  -H "X-API-Key: test-key-123"
```

---

## API Reference

### System

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health + record counts |

### 837P Claims

| Method | Path | Description |
|--------|------|-------------|
| POST | `/claims/ingest` | Upload an 837P EDI file |
| GET | `/claims/{claim_id}/status` | Look up a specific claim |

### 270 Eligibility

| Method | Path | Description |
|--------|------|-------------|
| POST | `/eligibility/ingest` | Upload a 270 EDI file |
| GET | `/eligibility/{inquiry_id}/status` | Look up a specific inquiry |

### Analytics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/analytics/claims/summary` | Total/avg/min/max claim amounts |
| GET | `/analytics/claims/recent` | Most recently ingested claims |
| GET | `/analytics/claims/by-sender` | Claim counts grouped by sender |
| GET | `/analytics/claims/top-diagnosis` | Most frequent diagnosis codes |
| GET | `/analytics/claims/top-procedures` | Most frequent procedure codes |
| GET | `/analytics/eligibility/summary` | Inquiry counts, unique members/payers |
| GET | `/analytics/eligibility/recent` | Most recently ingested inquiries |

All endpoints require `X-API-Key` header.

---

## Kafka (Optional)

Kafka adds async streaming for high-volume ingestion. The API works without it — Kafka publish failures are logged as warnings, not errors.

### Start Kafka locally

```bash
docker-compose up -d
```

Services:
- Kafka broker: `localhost:9092`
- Kafka UI: http://localhost:8080

### Run the consumer

```bash
python -m app.kafka.consumer
```

The consumer subscribes to `edi-837p-claims` and `edi-270-eligibility`, then writes every message to DuckDB.

---

## DuckDB Warehouse

Data is stored in `data/edi2insights.duckdb` (path configurable via `DUCKDB_PATH` env var).

### Query directly

```python
import duckdb
conn = duckdb.connect("data/edi2insights.duckdb")

# All claims
conn.execute("SELECT * FROM claims").df()

# Revenue by sender
conn.execute("""
    SELECT sender_id, COUNT(*) AS claims, SUM(claim_amount) AS revenue
    FROM claims GROUP BY sender_id ORDER BY revenue DESC
""").df()

# Member demographics
conn.execute("SELECT member_gender, COUNT(*) FROM eligibility_inquiries GROUP BY 1").df()
```

### Schema

**`claims`**

| Column | Type | Description |
|--------|------|-------------|
| claim_id | VARCHAR | UUID primary key |
| sender_id | VARCHAR | ISA06 — submitting clinic |
| receiver_id | VARCHAR | ISA08 — receiving payer |
| patient_name | VARCHAR | From NM1*QC segment |
| claim_amount | DOUBLE | From CLM segment |
| service_date | DATE | From DTP*472 segment |
| diagnosis_codes | VARCHAR[] | From HI segments |
| procedure_codes | VARCHAR[] | From SV1 segments |
| ingested_at | TIMESTAMP | Parse time (UTC) |

**`eligibility_inquiries`**

| Column | Type | Description |
|--------|------|-------------|
| inquiry_id | VARCHAR | UUID primary key |
| member_id | VARCHAR | Subscriber ID |
| member_last_name / first_name | VARCHAR | From NM1*IL |
| member_dob | DATE | From DMG segment |
| member_gender | VARCHAR | Male / Female / Unknown |
| payer_name / payer_id | VARCHAR | From NM1*PR |
| provider_npi | VARCHAR | From NM1*1P |
| service_types | JSON | Array of {code, description} |
| transaction_date | DATE | From BHT segment |

---

## Project Structure

```
EDI2Insights/
├── app/
│   ├── main.py                        # FastAPI app + lifespan
│   ├── auth.py                        # API key verification
│   ├── config.py                      # Pydantic settings (reads .env)
│   ├── parsers/
│   │   ├── edi_837p.py                # X12 837P parser
│   │   └── edi_270.py                 # X12 270 parser
│   ├── transformers/
│   │   ├── claims_transformer.py      # 837P → DuckDB
│   │   └── eligibility_transformer.py # 270 → DuckDB
│   ├── warehouse/
│   │   └── duckdb_client.py           # Connection + schema init
│   ├── kafka/
│   │   ├── producer.py                # Confluent producer
│   │   └── consumer.py                # Confluent consumer → DuckDB
│   ├── analytics/
│   │   └── reports.py                 # Query functions
│   └── routes/
│       ├── claims.py                  # /claims endpoints
│       ├── eligibility.py             # /eligibility endpoints
│       └── analytics.py               # /analytics endpoints
├── tests/
│   ├── sample_837p.edi                # Sample 837P transaction
│   ├── sample_270.edi                 # Sample 270 transaction
│   ├── test_parsers.py                # Parser unit tests
│   └── test_warehouse.py              # Warehouse integration tests
├── ingest_cli.py                      # CLI batch ingest tool
├── docker-compose.yml                 # Kafka + Zookeeper + Kafka UI
├── requirements.txt
└── .env                               # API key, Kafka, DuckDB path
```

---

## Configuration

All settings in `.env`:

```env
API_KEY=test-key-123
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_CLAIMS=edi-837p-claims
KAFKA_TOPIC_ELIGIBILITY=edi-270-eligibility
KAFKA_GROUP_ID=edi2insights-consumers
DUCKDB_PATH=data/edi2insights.duckdb
```

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| API | FastAPI | Async, auto-docs, type-safe |
| Parsing | Custom Python | Zero dependencies, X12-native |
| Streaming | Apache Kafka | Industry-standard EDI pipeline |
| Warehouse | **DuckDB** | Embedded OLAP, replaces BigQuery/Redshift — no account needed |
| Storage format | Parquet (via DuckDB) | Columnar, efficient analytics |
| Containerisation | Docker Compose | One-command Kafka setup |
