# app/parsers/edi_837p.py
import uuid
from datetime import datetime

def parse_837p(raw_edi: str) -> dict:
    """Parse an X12 837P EDI file into a structured dict."""
    segments = [s.strip() for s in raw_edi.split("~") if s.strip()]
    result = {
        "claim_id": str(uuid.uuid4()),
        "ingested_at": datetime.utcnow().isoformat(),
        "segment_count": len(segments),
        "sender_id": None,
        "receiver_id": None,
        "patient_name": None,
        "claim_amount": None,
        "service_date": None,
        "diagnosis_codes": [],
        "procedure_codes": [],
        "raw_segments": segments,
    }
    for seg in segments:
        elements = seg.split("*")
        seg_id = elements[0]
        if seg_id == "ISA" and len(elements) > 7:
            result["sender_id"]   = elements[6].strip()
            result["receiver_id"] = elements[8].strip()
        elif seg_id == "CLM" and len(elements) > 2:
            result["claim_amount"] = float(elements[2])
        elif seg_id == "HI":
            result["diagnosis_codes"] += [
                e.split(":")[1] for e in elements[1:] if ":" in e
            ]
        elif seg_id == "SV1" and len(elements) > 1:
            result["procedure_codes"].append(elements[1])
    return result