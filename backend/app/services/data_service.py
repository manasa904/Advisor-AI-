import sqlite3
import pandas as pd

DB_PATH = "../data/advisor_ai.db"

def get_db():
    return sqlite3.connect(DB_PATH)

def get_client(client_id: str):
    conn = get_db()
    df = pd.read_sql("SELECT * FROM clients WHERE client_id = ?", conn, params=[client_id])
    conn.close()
    return df.to_dict(orient="records")[0] if not df.empty else None

def get_portfolio(client_id: str):
    conn = get_db()
    df = pd.read_sql("SELECT * FROM portfolios WHERE client_id = ?", conn, params=[client_id])
    conn.close()
    return df.to_dict(orient="records")

def get_transactions(client_id: str, limit: int = 10):
    conn = get_db()
    df = pd.read_sql(
        "SELECT * FROM transactions WHERE client_id = ? ORDER BY txn_date DESC LIMIT ?",
        conn, params=[client_id, limit]
    )
    conn.close()
    return df.to_dict(orient="records")

def get_all_clients():
    conn = get_db()
    df = pd.read_sql("SELECT * FROM clients ORDER BY aum DESC", conn)
    conn.close()
    return df.to_dict(orient="records")

def get_high_risk_clients():
    conn = get_db()
    df = pd.read_sql("""
        SELECT client_id, sector,
               ROUND(SUM(current_value),2) as sector_value,
               ROUND(SUM(weight_pct),2) as total_weight
        FROM portfolios
        GROUP BY client_id, sector
        HAVING total_weight > 40
        ORDER BY total_weight DESC
    """, conn)
    conn.close()
    return df.to_dict(orient="records")