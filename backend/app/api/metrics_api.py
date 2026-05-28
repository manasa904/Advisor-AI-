from fastapi import APIRouter
from app.services.observability_service import get_system_metrics, log_request
from app.services.knowledge_graph_service import get_product_recommendations_for_client, get_client_product_network

router = APIRouter(prefix="/api/metrics", tags=["Observability"])

@router.get("")
def system_metrics():
    return get_system_metrics()

@router.get("/health/detailed")
def detailed_health():
    metrics = get_system_metrics()
    return {
        "status": "healthy",
        "services": {
            "fastapi": "running",
            "chromadb": "running",
            "sqlite": "running",
            "kafka": "running",
            "llm": "running"
        },
        "metrics_summary": {
            "total_api_calls": metrics["api_metrics"]["total_requests"],
            "avg_latency_ms": metrics["api_metrics"]["avg_latency_ms"],
            "error_rate": metrics["api_metrics"]["error_rate_pct"],
            "open_anomalies": metrics["data_summary"]["open_anomalies"],
            "open_violations": metrics["data_summary"]["open_violations"]
        }
    }

knowledge_router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Graph"])

@knowledge_router.get("/products/{client_id}")
def product_recommendations(client_id: str):
    return get_product_recommendations_for_client(client_id)

@knowledge_router.get("/network/{client_id}")
def client_network(client_id: str):
    return get_client_product_network(client_id)