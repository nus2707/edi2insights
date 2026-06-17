import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import claims, eligibility, analytics
from app.warehouse.duckdb_client import get_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_connection()  # initialise schema on startup
    yield


app = FastAPI(
    title="EDI2Insights API",
    description=(
        "End-to-end healthcare EDI pipeline. "
        "Ingests X12 837P claims and 270 eligibility files, "
        "stores them in DuckDB, and exposes analytics endpoints."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(claims.router,    prefix="/claims",      tags=["837P Claims"])
app.include_router(eligibility.router, prefix="/eligibility", tags=["270 Eligibility"])
app.include_router(analytics.router,  prefix="/analytics",   tags=["Analytics"])


@app.get("/health", tags=["System"])
async def health():
    conn = get_connection()
    claim_count  = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    inquiry_count = conn.execute("SELECT COUNT(*) FROM eligibility_inquiries").fetchone()[0]
    return {
        "status":          "ok",
        "service":         "EDI2Insights",
        "claims_stored":   claim_count,
        "inquiries_stored": inquiry_count,
    }
