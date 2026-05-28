from fastapi import APIRouter
import sqlite3
import pandas as pd

router = APIRouter(prefix="/api/operations", tags=["Operations"])

DB_PATH = "../data/advisor_ai.db"

def get_db():
    return sqlite3.connect(DB_PATH)

@router.get("/summary")
def operations_summary():
    conn = get_db()
    clients_df = pd.read_sql("SELECT COUNT(*) as total, segment, COUNT(*) as count FROM clients GROUP BY segment", conn)
    txn_df = pd.read_sql("""
        SELECT
            COUNT(*) as total_transactions,
            SUM(CASE WHEN txn_type='BUY' THEN 1 ELSE 0 END) as buys,
            SUM(CASE WHEN txn_type='SELL' THEN 1 ELSE 0 END) as sells,
            SUM(amount) as total_value
        FROM transactions
    """, conn)
    aum_df = pd.read_sql("SELECT SUM(aum) as total_aum, COUNT(*) as total_clients FROM clients", conn)
    conn.close()
    return {
        "aum_summary": aum_df.to_dict(orient="records")[0],
        "transaction_summary": txn_df.to_dict(orient="records")[0],
        "client_segments": clients_df.to_dict(orient="records")
    }

@router.get("/transactions")
def all_transactions():
    conn = get_db()
    df = pd.read_sql("""
        SELECT t.*, c.name as client_name, c.segment, c.relationship_manager
        FROM transactions t
        JOIN clients c ON t.client_id = c.client_id
        ORDER BY t.txn_date DESC
    """, conn)
    conn.close()
    return df.to_dict(orient="records")

@router.get("/rm-summary")
def rm_summary():
    conn = get_db()
    df = pd.read_sql("""
        SELECT relationship_manager,
               COUNT(*) as client_count,
               SUM(aum) as total_aum,
               AVG(aum) as avg_aum
        FROM clients
        GROUP BY relationship_manager
        ORDER BY total_aum DESC
    """, conn)
    conn.close()
    return df.to_dict(orient="records")