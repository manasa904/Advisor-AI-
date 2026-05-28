from fastapi import APIRouter
from app.services.ner_service import extract_entities, enrich_query_with_entities
from app.services.anomaly_service import detect_all_anomalies, get_anomalies_for_client
from pydantic import BaseModel

router = APIRouter(prefix="/api/analytics", tags=["Analytics & AI"])

class NERRequest(BaseModel):
    text: str

@router.post("/ner")
def named_entity_recognition(request: NERRequest):
    entities = extract_entities(request.text)
    enriched = enrich_query_with_entities(request.text, entities)
    return {"original": request.text, "entities": entities, "enriched_query": enriched}

@router.get("/anomalies")
def run_anomaly_detection():
    anomalies = detect_all_anomalies()
    critical = [a for a in anomalies if a["severity"] == "HIGH"]
    return {"total_anomalies": len(anomalies), "critical_count": len(critical), "anomalies": anomalies}

@router.get("/anomalies/{client_id}")
def client_anomalies(client_id: str):
    anomalies = get_anomalies_for_client(client_id)
    return {"client_id": client_id, "anomaly_count": len(anomalies), "anomalies": anomalies}