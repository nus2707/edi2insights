from fastapi import APIRouter, Depends
from app.auth import verify_api_key
from app.analytics import reports

router = APIRouter()


@router.get("/claims/summary")
async def claims_summary(_: str = Depends(verify_api_key)):
    return reports.claims_summary()


@router.get("/claims/recent")
async def recent_claims(limit: int = 20, _: str = Depends(verify_api_key)):
    return reports.recent_claims(limit)


@router.get("/claims/by-sender")
async def claims_by_sender(_: str = Depends(verify_api_key)):
    return reports.claims_by_sender()


@router.get("/claims/top-diagnosis")
async def top_diagnosis(limit: int = 10, _: str = Depends(verify_api_key)):
    return reports.top_diagnosis_codes(limit)


@router.get("/claims/top-procedures")
async def top_procedures(limit: int = 10, _: str = Depends(verify_api_key)):
    return reports.top_procedure_codes(limit)


@router.get("/eligibility/summary")
async def eligibility_summary(_: str = Depends(verify_api_key)):
    return reports.eligibility_summary()


@router.get("/eligibility/recent")
async def recent_inquiries(limit: int = 20, _: str = Depends(verify_api_key)):
    return reports.recent_inquiries(limit)
