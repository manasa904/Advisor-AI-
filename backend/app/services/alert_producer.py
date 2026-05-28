import json
import threading
from datetime import datetime
from kafka import KafkaProducer
import time
import random

KAFKA_BOOTSTRAP = "localhost:9092"
ALERT_TOPIC     = "advisor.alerts"

def get_producer():
    try:
        return KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None
        )
    except Exception as e:
        print(f"Kafka producer error: {e}")
        return None

def publish_alert(alert_type: str, client_id: str, message: str,
                  severity: str = "INFO", ticker: str = None, details: dict = {}):
    producer = get_producer()
    if not producer:
        return False
    alert = {
        "alert_id":   f"ALT-{int(time.time()*1000)}",
        "timestamp":  datetime.now().isoformat(),
        "alert_type": alert_type,
        "client_id":  client_id,
        "severity":   severity,
        "message":    message,
        "ticker":     ticker,
        "details":    details
    }
    try:
        producer.send(ALERT_TOPIC, key=client_id, value=alert)
        producer.flush()
        producer.close()
        return True
    except Exception as e:
        print(f"Failed to publish alert: {e}")
        return False

# ── Simulated Real-Time Alert Stream ───────────────────────────────────────
SIMULATED_ALERTS = [
    {"type":"PRICE_ALERT",       "client":"C001","severity":"HIGH",
     "msg":"AAPL dropped 3.2% in last 30 minutes — below advisor alert threshold.",
     "ticker":"AAPL","details":{"change_pct":-3.2,"current_price":183.0,"threshold_price":185.0}},
    {"type":"CONCENTRATION_RISK","client":"C002","severity":"HIGH",
     "msg":"C002 Technology sector now at 72% — exceeds 40% concentration limit.",
     "ticker":None,"details":{"sector":"Technology","current_pct":72.0,"limit":40.0}},
    {"type":"COMPLIANCE_ALERT",  "client":"C003","severity":"CRITICAL",
     "msg":"Attempted purchase of restricted security GME flagged and blocked.",
     "ticker":"GME","details":{"rule":"RestrictedList","action":"BUY"}},
    {"type":"MARKET_ALERT",      "client":"ALL", "severity":"MEDIUM",
     "msg":"RBI rate decision: Repo rate held at 6.5%. Bond portfolios may see repricing.",
     "ticker":None,"details":{"event":"RBI_RATE_DECISION","rate":6.5}},
    {"type":"PRICE_ALERT",       "client":"C005","severity":"HIGH",
     "msg":"TATAMOTORS up 8.5% today — consider booking partial profits.",
     "ticker":"TATAMOTORS","details":{"change_pct":8.5,"current_price":737.0}},
    {"type":"REBALANCE_ALERT",   "client":"C006","severity":"MEDIUM",
     "msg":"C006 portfolio drifted 15% from target — rebalancing recommended.",
     "ticker":None,"details":{"drift_pct":15.0,"recommendation":"Reduce Financials, Add Bonds"}},
    {"type":"LIFE_EVENT",        "client":"C003","severity":"INFO",
     "msg":"Client Suresh Patel turns 62 next month — review RMD requirements.",
     "ticker":None,"details":{"event":"AGE_MILESTONE","age":62}},
    {"type":"TRADE_ALERT",       "client":"C004","severity":"INFO",
     "msg":"Large trade detected: SBIN BUY ₹580,000 — post-trade review required.",
     "ticker":"SBIN","details":{"trade_value":580000,"action":"BUY"}},
]

def simulate_alert_stream(interval_seconds: int = 8):
    """Continuously publish simulated alerts to Kafka"""
    print(f"Starting alert simulation — publishing every {interval_seconds}s")
    idx = 0
    while True:
        alert = SIMULATED_ALERTS[idx % len(SIMULATED_ALERTS)]
        success = publish_alert(
            alert_type=alert["type"],
            client_id=alert["client"],
            message=alert["msg"],
            severity=alert["severity"],
            ticker=alert.get("ticker"),
            details=alert.get("details", {})
        )
        if success:
            print(f"Published alert: [{alert['severity']}] {alert['type']} — {alert['client']}")
        idx += 1
        time.sleep(interval_seconds)

def start_alert_simulation_background(interval_seconds: int = 8):
    thread = threading.Thread(
        target=simulate_alert_stream,
        args=(interval_seconds,),
        daemon=True
    )
    thread.start()
    return thread