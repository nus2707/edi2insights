# app/parsers/edi_270.py
import uuid
from datetime import datetime

SERVICE_TYPE_CODES = {
    "1":  "Medical Care",           "30": "Health Benefit Plan",
    "35": "Dental Care",            "48": "Hospital - Inpatient",
    "50": "Hospital - Outpatient",  "86": "Emergency Services",
    "98": "Professional (Physician)",
}
GENDER_MAP = {"M": "Male", "F": "Female", "U": "Unknown"}

def _parse_date(raw: str) -> str | None:
    """Convert CCYYMMDD → ISO YYYY-MM-DD."""
    if not raw or len(raw) != 8:
        return None
    try:
        return datetime.strptime(raw, "%Y%m%d").date().isoformat()
    except ValueError:
        return None

def _safe_get(elements: list, index: int, default=None):
    try:
        val = elements[index].strip()
        return val if val else default
    except IndexError:
        return default

def parse_270(raw_edi: str) -> dict:
    segments = [s.strip() for s in raw_edi.split("~") if s.strip()]

    result = {
        "inquiry_id":        str(uuid.uuid4()),
        "ingested_at":       datetime.utcnow().isoformat(),
        "transaction_date":  None,
        "reference_id":      None,   # BHT03
        "sender_id":         None,   # ISA06
        "receiver_id":       None,   # ISA08
        "payer_name":        None,
        "payer_id":          None,
        "provider_npi":      None,
        "provider_name":     None,
        "member_id":         None,
        "member_last_name":  None,
        "member_first_name": None,
        "member_dob":        None,
        "member_gender":     None,
        "service_types":     [],
        "segment_count":     len(segments),
    }

    for seg in segments:
        el = seg.split("*")
        seg_id = el[0]

        if seg_id == "ISA":
            result["sender_id"]   = _safe_get(el, 6)
            result["receiver_id"] = _safe_get(el, 8)

        elif seg_id == "BHT":
            result["reference_id"]    = _safe_get(el, 3)
            result["transaction_date"] = _parse_date(_safe_get(el, 4, ""))

        elif seg_id == "NM1":
            qualifier = _safe_get(el, 1)
            if qualifier == "PR":        # Payer
                result["payer_name"] = _safe_get(el, 3)
                result["payer_id"]   = _safe_get(el, 9)
            elif qualifier == "1P":      # Provider
                result["provider_name"] = _safe_get(el, 3)
                result["provider_npi"]  = _safe_get(el, 9)
            elif qualifier == "IL":      # Subscriber / member
                result["member_last_name"]  = _safe_get(el, 3)
                result["member_first_name"] = _safe_get(el, 4)
                result["member_id"]         = _safe_get(el, 9)

        elif seg_id == "DMG":
            result["member_dob"]    = _parse_date(_safe_get(el, 2, ""))
            result["member_gender"] = GENDER_MAP.get(_safe_get(el, 3, "U"), "Unknown")

        elif seg_id == "EQ":
            code = _safe_get(el, 1)
            result["service_types"].append({
                "code":        code,
                "description": SERVICE_TYPE_CODES.get(code, f"Unknown ({code})"),
            })

    return result