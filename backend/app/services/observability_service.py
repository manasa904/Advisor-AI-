import sqlite3
import pandas as pd
import time
import logging
import json
from datetime import datetime
from functools import wraps
from typing import Callable

DB_PATH = "../data/advisor_ai.db"
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s - %(message)s')
logger = logging.getLogger("advisor-ai")

def get_db():
    return sqlite3.connect(DB_PATH)

def ensure_metrics_tables():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT, method TEXT, status_code INTEGER,
            latency_ms REAL, user_role TEXT, client_id TEXT,
            request_size INTEGER, response_size INTEGER, logged_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_performance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT, query_type TEXT, input_length INTEGER,
            output_length INTEGER, latency_ms REAL,
            retrieved_chunks INTEGER, success INTEGER, logged_at TEXT
        )
    """)
    conn.commit()
    conn.close()

ensure_metrics_tables()

def log_request(endpoint: str, method: str, status_code: int, latency_ms: float,
                user_role: str = None, client_id: str = None):
    conn = get_db()
    conn.execute("""
        INSERT INTO request_logs (endpoint, method, status_code, latency_ms, user_role, client_id, logged_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (endpoint, method, status_code, latency_ms, user_role, client_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    logger.info(json.dumps({"endpoint": endpoint, "method": method, "status": status_code,
                            "latency_ms": round(latency_ms, 2), "role": user_role}))

def log_ai_call(model: str, query_type: str, input_length: int, output_length: int,
                latency_ms: float, retrieved_chunks: int = 0, success: bool = True):
    conn = get_db()
    conn.execute("""
        INSERT INTO ai_performance_log (model, query_type, input_length, output_length,
        latency_ms, retrieved_chunks, success, logged_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (model, query_type, input_length, output_length, latency_ms, retrieved_chunks,
          1 if success else 0, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_system_metrics() -> dict:
    conn = get_db()

    req_df = pd.read_sql("""
        SELECT COUNT(*) as total, AVG(latency_ms) as avg_latency,
               SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors,
               MIN(logged_at) as first_request, MAX(logged_at) as last_request
        FROM request_logs
    """, conn)

    endpoint_df = pd.read_sql("""
        SELECT endpoint, COUNT(*) as calls, AVG(latency_ms) as avg_latency,
               SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors
        FROM request_logs GROUP BY endpoint ORDER BY calls DESC LIMIT 10
    """, conn)

    ai_df = pd.read_sql("""
        SELECT model, COUNT(*) as calls, AVG(latency_ms) as avg_latency,
               SUM(CASE WHEN success=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) as success_rate,
               AVG(retrieved_chunks) as avg_chunks
        FROM ai_performance_log GROUP BY model
    """, conn)

    role_df = pd.read_sql("""
        SELECT user_role, COUNT(*) as requests FROM request_logs
        WHERE user_role IS NOT NULL GROUP BY user_role
    """, conn)

    client_df = pd.read_sql("SELECT COUNT(*) as total FROM clients", conn)
    portfolio_df = pd.read_sql("SELECT COUNT(*) as total FROM portfolios", conn)
    txn_df = pd.read_sql("SELECT COUNT(*) as total FROM transactions", conn)
    violations_df = pd.read_sql("SELECT COUNT(*) as total FROM compliance_audit WHERE result='FAIL'", conn)
    alerts_df = pd.read_sql("SELECT COUNT(*) as total FROM anomaly_flags WHERE resolved=0", conn) if _table_exists(conn, "anomaly_flags") else pd.DataFrame([{"total": 0}])

    conn.close()

    req = req_df.iloc[0]
    return {
        "system_health": "healthy",
        "timestamp": datetime.now().isoformat(),
        "api_metrics": {
            "total_requests": int(req["total"] or 0),
            "avg_latency_ms": round(float(req["avg_latency"] or 0), 2),
            "error_count": int(req["errors"] or 0),
            "error_rate_pct": round(float(req["errors"] or 0) / max(int(req["total"] or 1), 1) * 100, 2),
            "top_endpoints": endpoint_df.to_dict(orient="records")
        },
        "ai_metrics": ai_df.to_dict(orient="records"),
        "user_activity": role_df.to_dict(orient="records"),
        "data_summary": {
            "total_clients": int(client_df.iloc[0]["total"]),
            "total_holdings": int(portfolio_df.iloc[0]["total"]),
            "total_transactions": int(txn_df.iloc[0]["total"]),
            "open_violations": int(violations_df.iloc[0]["total"]),
            "open_anomalies": int(alerts_df.iloc[0]["total"])
        }
    }

def _table_exists(conn, table_name):
    result = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
    return result is not None