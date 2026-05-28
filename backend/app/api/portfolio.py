from fastapi import APIRouter, HTTPException
from app.services.data_service import (
    get_client, get_portfolio, get_transactions,
    get_all_clients, get_high_risk_clients
)

router = APIRouter(tags=["Portfolio"])

@router.get("/clients")
def list_clients():
    return get_all_clients()

@router.get("/clients/{client_id}")
def client_detail(client_id: str):
    client = get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.get("/clients/{client_id}/holdings")
def client_holdings(client_id: str):
    return get_portfolio(client_id)

@router.get("/clients/{client_id}/transactions")
def client_transactions(client_id: str):
    return get_transactions(client_id)

@router.get("/risk/concentration")
def concentration_risk():
    return get_high_risk_clients()