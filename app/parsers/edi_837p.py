import uuid
from datetime import datetime


def parse_837p(raw_edi: str) -> dict:
    """Parse an X12 837P EDI file into a structured dict."""
    segments = [s.strip() for s in raw_edi.split("~") if s.strip()]
    result = {
        "claim_id":        str(uuid.uuid4()),
        "ingested_at":     datetime.utcnow().isoformat(),
        "segment_count":   len(segments),
        "sender_id":       None,
        "receiver_id":     None,
        "patient_name":    None,
        "claim_amount":    None,
        "service_date":    None,
        "diagnosis_codes": [],
        "procedure_codes": [],
        "raw_segments":    segments,
    }

    for seg in segments:
        elements = seg.split("*")
        seg_id = elements[0]

        if seg_id == "ISA" and len(elements) > 8:
            result["sender_id"]   = elements[6].strip()
            result["receiver_id"] = elements[8].strip()

        elif seg_id == "NM1" and len(elements) > 4:
            qualifier = elements[1]
            if qualifier == "QC":  # patient
                last  = elements[3].strip() if len(elements) > 3 else ""
                first = elements[4].strip() if len(elements) > 4 else ""
                result["patient_name"] = f"{first} {last}".strip() or None

        elif seg_id == "CLM" and len(elements) > 2:
            try:
                result["claim_amount"] = float(elements[2])
            except (ValueError, IndexError):
                pass

        elif seg_id == "DTP" and len(elements) > 3 and elements[1] == "472":
            raw_date = elements[3].strip()
            if len(raw_date) == 8:
                result["service_date"] = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"

        elif seg_id == "HI":
            for e in elements[1:]:
                if ":" in e:
                    result["diagnosis_codes"].append(e.split(":")[1])

        elif seg_id == "SV1" and len(elements) > 1:
            code = elements[1]
            if ":" in code:
                code = code.split(":")[1]
            result["procedure_codes"].append(code)

    return result
