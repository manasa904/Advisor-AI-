import sqlite3
import pandas as pd
from datetime import datetime
from typing import Optional, List

DB_PATH = "../data/advisor_ai.db"

def get_db():
    return sqlite3.connect(DB_PATH)

def ensure_governance_tables():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS model_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL, version TEXT NOT NULL,
            description TEXT, status TEXT DEFAULT 'active',
            deployed_at TEXT, total_calls INTEGER DEFAULT 0,
            avg_latency_ms REAL DEFAULT 0, error_rate REAL DEFAULT 0,
            last_called TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hitl_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_type TEXT NOT NULL, client_id TEXT,
            advisor_id TEXT, details TEXT, status TEXT DEFAULT 'pending',
            submitted_at TEXT, reviewed_at TEXT,
            reviewer_id TEXT, reviewer_note TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversation_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL, user_id TEXT NOT NULL,
            role TEXT NOT NULL, content TEXT NOT NULL,
            timestamp TEXT NOT NULL, client_context TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS model_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT, version TEXT, caller TEXT,
            input_tokens INTEGER, output_tokens INTEGER,
            latency_ms REAL, success INTEGER, error_msg TEXT,
            called_at TEXT
        )
    """)
    # Seed model registry
    existing = pd.read_sql("SELECT COUNT(*) as cnt FROM model_registry", conn).iloc[0]["cnt"]
    if existing == 0:
        models = [
            ("RAG Pipeline", "1.0", "Retrieval-Augmented Generation for advisor queries", "active"),
            ("Compliance Engine", "2.0", "Pre/post-trade compliance rule engine", "active"),
            ("NBA Engine", "1.0", "Next-Best-Action recommendation engine", "active"),
            ("NER Model", "1.0", "Financial entity recognition", "active"),
            ("Anomaly Detector", "1.0", "Portfolio anomaly detection", "active"),
        ]
        for m in models:
            conn.execute("INSERT INTO model_registry (model_name, version, description, status, deployed_at) VALUES (?,?,?,?,?)",
                        (*m, datetime.now().isoformat()))
    conn.commit()
    conn.close()

ensure_governance_tables()

def log_model_call(model_name: str, version: str, caller: str, latency_ms: float, success: bool, error_msg: str = None):
    conn = get_db()
    conn.execute("""
        INSERT INTO model_calls (model_name, version, caller, latency_ms, success, error_msg, called_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (model_name, version, caller, latency_ms, 1 if success else 0, error_msg, datetime.now().isoformat()))
    conn.execute("""
        UPDATE model_registry SET total_calls = total_calls + 1, last_called = ?
        WHERE model_name = ? AND version = ?
    """, (datetime.now().isoformat(), model_name, version))
    conn.commit()
    conn.close()

def submit_hitl(request_type: str, client_id: str, advisor_id: str, details: str) -> dict:
    conn = get_db()
    cursor = conn.execute("""
        INSERT INTO hitl_queue (request_type, client_id, advisor_id, details, status, submitted_at)
        VALUES (?, ?, ?, ?, 'pending', ?)
    """, (request_type, client_id, advisor_id, details, datetime.now().isoformat()))
    hitl_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"hitl_id": hitl_id, "status": "submitted", "message": "Request submitted for human review."}

def review_hitl(hitl_id: int, reviewer_id: str, decision: str, note: str) -> dict:
    conn = get_db()
    conn.execute("""
        UPDATE hitl_queue SET status=?, reviewer_id=?, reviewer_note=?, reviewed_at=?
        WHERE id=?
    """, (decision, reviewer_id, note, datetime.now().isoformat(), hitl_id))
    conn.commit()
    conn.close()
    return {"hitl_id": hitl_id, "decision": decision, "reviewed_by": reviewer_id}

def get_hitl_queue(status: str = "pending") -> list:
    conn = get_db()
    df = pd.read_sql("SELECT * FROM hitl_queue WHERE status=? ORDER BY submitted_at DESC", conn, params=[status])
    conn.close()
    return df.to_dict(orient="records")

def save_conversation(session_id: str, user_id: str, role: str, content: str, client_context: str = None):
    conn = get_db()
    conn.execute("""
        INSERT INTO conversation_memory (session_id, user_id, role, content, timestamp, client_context)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, user_id, role, content, datetime.now().isoformat(), client_context))
    conn.commit()
    conn.close()

def get_conversation_history(session_id: str, limit: int = 20) -> list:
    conn = get_db()
    df = pd.read_sql("""
        SELECT role, content, timestamp, client_context FROM conversation_memory
        WHERE session_id=? ORDER BY timestamp DESC LIMIT ?
    """, conn, params=[session_id, limit])
    conn.close()
    return list(reversed(df.to_dict(orient="records")))

def get_model_registry() -> list:
    conn = get_db()
    df = pd.read_sql("SELECT * FROM model_registry ORDER BY model_name", conn)
    conn.close()
    return df.to_dict(orient="records")

def get_model_performance() -> dict:
    conn = get_db()
    df = pd.read_sql("""
        SELECT model_name, COUNT(*) as calls, AVG(latency_ms) as avg_latency,
               SUM(CASE WHEN success=1 THEN 1 ELSE 0 END)*100.0/COUNT(*) as success_rate
        FROM model_calls GROUP BY model_name
    """, conn)
    conn.close()
    return df.to_dict(orient="records")