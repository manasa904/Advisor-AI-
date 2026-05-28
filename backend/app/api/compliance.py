from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.compliance_service import (
    run_pretrade_check, get_audit_log,
    get_violations_summary
)

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])

class PreTradeRequest(BaseModel):
    client_id: str
    ticker: str
    sector: str
    action: str       # BUY or SELL
    quantity: int
    price: float

@router.post("/pretrade-check")
def pretrade_check(request: PreTradeRequest):
    return run_pretrade_check(
        client_id=request.client_id,
        ticker=request.ticker,
        sector=request.sector,
        action=request.action,
        quantity=request.quantity,
        price=request.price
    )

@router.get("/audit-log")
def audit_log(client_id: Optional[str] = None, limit: int = 50):
    return get_audit_log(client_id=client_id, limit=limit)

@router.get("/violations-summary")
def violations_summary():
    return get_violations_summary()