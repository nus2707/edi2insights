#!/usr/bin/env python
"""
CLI tool to ingest one or more EDI files directly into DuckDB
(no API server or Kafka required).

Usage:
    python ingest_cli.py tests/sample_837p.edi
    python ingest_cli.py tests/sample_270.edi
    python ingest_cli.py tests/*.edi
"""
import sys
import json
from pathlib import Path

from app.parsers.edi_837p import parse_837p
from app.parsers.edi_270 import parse_270
from app.transformers.claims_transformer import store_claim
from app.transformers.eligibility_transformer import store_inquiry
from app.analytics.reports import claims_summary, eligibility_summary


def detect_type(raw: str) -> str:
    for seg in raw.split("~"):
        if seg.strip().startswith("ST*"):
            parts = seg.split("*")
            if len(parts) > 1:
                return parts[1].strip()
    return "unknown"


def ingest(path: Path) -> None:
    raw = path.read_text(encoding="utf-8")
    edi_type = detect_type(raw)

    if edi_type == "837":
        parsed = parse_837p(raw)
        store_claim(parsed)
        print(f"[837P] {path.name} -> claim_id={parsed['claim_id']} amount=${parsed.get('claim_amount')}")
    elif edi_type == "270":
        parsed = parse_270(raw)
        store_inquiry(parsed)
        print(f"[270]  {path.name} -> inquiry_id={parsed['inquiry_id']} member={parsed.get('member_first_name')} {parsed.get('member_last_name')}")
    else:
        print(f"[SKIP] {path.name} — unknown EDI type '{edi_type}'")


def main():
    if len(sys.argv) < 2:
        print("Usage: python ingest_cli.py <file.edi> [file2.edi ...]")
        sys.exit(1)

    for pattern in sys.argv[1:]:
        paths = list(Path(".").glob(pattern)) if "*" in pattern else [Path(pattern)]
        for p in paths:
            if p.exists():
                ingest(p)
            else:
                print(f"[WARN] File not found: {p}")

    print("\n--- Summary ---")
    print("Claims:     ", json.dumps(claims_summary(), indent=2))
    print("Eligibility:", json.dumps(eligibility_summary(), indent=2))


if __name__ == "__main__":
    main()
