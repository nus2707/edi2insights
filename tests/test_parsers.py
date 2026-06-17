import pytest
from app.parsers.edi_837p import parse_837p
from app.parsers.edi_270 import parse_270

SAMPLE_837P = (
    "ISA*00*          *00*          *ZZ*CLINIC001      *ZZ*PAYER999       "
    "*240601*1032*^*00501*000000001*0*P*:~"
    "GS*HC*CLINIC001*PAYER999*20240601*1032*1*X*005010X222A1~"
    "ST*837*0001*005010X222A1~"
    "BHT*0019*00*CLAIM001*20240601*1032*CH~"
    "NM1*41*2*CLINIC ONE*****46*CLINIC001~"
    "NM1*40*2*PAYER999*****46*PAYER999~"
    "HL*1**20*1~"
    "NM1*85*2*CLINIC ONE*****XX*1234567890~"
    "HL*2*1*22*0~"
    "NM1*QC*1*DOE*JOHN****MI*MEM123456~"
    "CLM*CLAIM-001*1250.00***11:B:1*Y*A*Y*I~"
    "HI*ABK:J069~"
    "SV1*HC:99213*150.00*UN*1***1~"
    "SE*13*0001~GE*1*1~IEA*1*000000001~"
)

SAMPLE_270 = (
    "ISA*00*          *00*          *ZZ*CLINIC001      *ZZ*PAYER999       "
    "*240601*1032*^*00501*000000001*0*P*:~"
    "GS*HS*CLINIC001*PAYER999*20240601*1032*1*X*005010X279A1~"
    "ST*270*0001*005010X279A1~"
    "BHT*0022*13*10001234*20240601*1032~"
    "HL*1**20*1~"
    "NM1*PR*2*BLUE CROSS*****PI*PAYER999~"
    "HL*2*1*21*1~"
    "NM1*1P*2*CLINIC ONE*****XX*1234567890~"
    "HL*3*2*22*0~"
    "NM1*IL*1*DOE*JOHN****MI*ABC123456789~"
    "DMG*D8*19800515*M~"
    "EQ*30~"
    "SE*12*0001~GE*1*1~IEA*1*000000001~"
)


class TestParse837P:
    def test_returns_dict(self):
        result = parse_837p(SAMPLE_837P)
        assert isinstance(result, dict)

    def test_claim_id_is_uuid(self):
        import uuid
        result = parse_837p(SAMPLE_837P)
        uuid.UUID(result["claim_id"])  # raises if invalid

    def test_sender_receiver(self):
        result = parse_837p(SAMPLE_837P)
        assert result["sender_id"] == "CLINIC001"
        assert result["receiver_id"] == "PAYER999"

    def test_claim_amount(self):
        result = parse_837p(SAMPLE_837P)
        assert result["claim_amount"] == 1250.00

    def test_diagnosis_codes(self):
        result = parse_837p(SAMPLE_837P)
        assert "J069" in result["diagnosis_codes"]

    def test_procedure_codes(self):
        result = parse_837p(SAMPLE_837P)
        assert "99213" in result["procedure_codes"]

    def test_patient_name(self):
        result = parse_837p(SAMPLE_837P)
        assert "DOE" in (result["patient_name"] or "")

    def test_segment_count(self):
        result = parse_837p(SAMPLE_837P)
        assert result["segment_count"] > 0


class TestParse270:
    def test_returns_dict(self):
        result = parse_270(SAMPLE_270)
        assert isinstance(result, dict)

    def test_member_info(self):
        result = parse_270(SAMPLE_270)
        assert result["member_last_name"] == "DOE"
        assert result["member_first_name"] == "JOHN"
        assert result["member_id"] == "ABC123456789"

    def test_member_dob(self):
        result = parse_270(SAMPLE_270)
        assert result["member_dob"] == "1980-05-15"

    def test_member_gender(self):
        result = parse_270(SAMPLE_270)
        assert result["member_gender"] == "Male"

    def test_payer_info(self):
        result = parse_270(SAMPLE_270)
        assert result["payer_name"] == "BLUE CROSS"
        assert result["payer_id"] == "PAYER999"

    def test_service_types(self):
        result = parse_270(SAMPLE_270)
        assert len(result["service_types"]) > 0
        codes = [s["code"] for s in result["service_types"]]
        assert "30" in codes

    def test_transaction_date(self):
        result = parse_270(SAMPLE_270)
        assert result["transaction_date"] == "2024-06-01"
