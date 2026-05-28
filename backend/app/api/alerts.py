import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.alert_producer import publish_alert, start_alert_simulation_background
from app.services.alert_consumer import alert_manager, start_kafka_consumer_background
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

# Start consumer and simulation on import
start_kafka_consumer_background()
start_alert_simulation_background(interval_seconds=8)

class ManualAlert(BaseModel):
    alert_type: str
    client_id: str
    message: str
    severity: str = "INFO"
    ticker: Optional[str] = None

@router.websocket("/ws")
async def websocket_alerts(websocket: WebSocket):
    alert_manager.set_loop(asyncio.get_event_loop())
    await alert_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        await alert_manager.disconnect(websocket)

@router.get("/recent")
def get_recent_alerts():
    return {
        "alerts": list(reversed(alert_manager.recent_alerts)),
        "count": len(alert_manager.recent_alerts)
    }

@router.post("/publish")
def publish_manual_alert(alert: ManualAlert):
    success = publish_alert(
        alert_type=alert.alert_type,
        client_id=alert.client_id,
        message=alert.message,
        severity=alert.severity,
        ticker=alert.ticker
    )
    return {"success": success, "message": "Alert published" if success else "Kafka unavailable"}