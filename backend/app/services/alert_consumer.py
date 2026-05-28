import json
import threading
import asyncio
from datetime import datetime
from typing import Set
from fastapi import WebSocket
from kafka import KafkaConsumer

KAFKA_BOOTSTRAP = "localhost:9092"
ALERT_TOPIC     = "advisor.alerts"

# ── WebSocket Connection Manager ───────────────────────────────────────────
class AlertManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.recent_alerts: list = []
        self.max_recent = 50
        self._loop = None

    def set_loop(self, loop):
        self._loop = loop

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        # Send recent alerts to newly connected client
        for alert in self.recent_alerts[-10:]:
            try:
                await websocket.send_text(json.dumps(alert))
            except:
                pass

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, alert: dict):
        self.recent_alerts.append(alert)
        if len(self.recent_alerts) > self.max_recent:
            self.recent_alerts = self.recent_alerts[-self.max_recent:]

        dead = set()
        for ws in self.active_connections:
            try:
                await ws.send_text(json.dumps(alert))
            except:
                dead.add(ws)
        self.active_connections -= dead

    def broadcast_sync(self, alert: dict):
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.broadcast(alert), self._loop)

alert_manager = AlertManager()

# ── Kafka Consumer Thread ──────────────────────────────────────────────────
def run_kafka_consumer():
    print("Starting Kafka alert consumer...")
    try:
        consumer = KafkaConsumer(
            ALERT_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
            group_id="advisor-ai-alerts",
            consumer_timeout_ms=1000
        )
        while True:
            try:
                for msg in consumer:
                    alert_manager.broadcast_sync(msg.value)
            except Exception:
                pass
    except Exception as e:
        print(f"Kafka consumer error: {e}")

def start_kafka_consumer_background():
    thread = threading.Thread(target=run_kafka_consumer, daemon=True)
    thread.start()
    return thread