import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict

DB_PATH = "../data/advisor_ai.db"

def get_db():
    return sqlite3.connect(DB_PATH)

def ensure_anomaly_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS anomaly_flags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT, ticker TEXT, anomaly_type TEXT,
            severity TEXT, description TEXT, value REAL,
            threshold REAL, detected_at TEXT, resolved INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

ensure_anomaly_table()

def detect_all_anomalies() -> List[Dict]:
    conn = get_db()
    portfolios = pd.read_sql("SELECT * FROM portfolios", conn)
    transactions = pd.read_sql("SELECT * FROM transactions", conn)
    clients = pd.read_sql("SELECT * FROM clients", conn)
    conn.close()

    anomalies = []

    # 1. Concentration anomaly per client
    for client_id, group in portfolios.groupby("client_id"):
        total = group["current_value"].sum()
        for _, row in group.iterrows():
            pct = row["current_value"] / total * 100 if total > 0 else 0
            if pct > 35:
                anomalies.append({
                    "client_id": client_id, "ticker": row["ticker"],
                    "anomaly_type": "CONCENTRATION", "severity": "HIGH" if pct > 50 else "MEDIUM",
                    "description": f"{row['ticker']} is {pct:.1f}% of portfolio — exceeds 35% single-holding limit.",
                    "value": round(pct, 2), "threshold": 35.0, "detected_at": datetime.now().isoformat()
                })

    # 2. Sector concentration
    for client_id, group in portfolios.groupby("client_id"):
        total = group["current_value"].sum()
        for sector, sgrp in group.groupby("sector"):
            spct = sgrp["current_value"].sum() / total * 100 if total > 0 else 0
            if spct > 60:
                anomalies.append({
                    "client_id": client_id, "ticker": None,
                    "anomaly_type": "SECTOR_CONCENTRATION", "severity": "HIGH",
                    "description": f"{sector} sector is {spct:.1f}% of portfolio — extreme concentration.",
                    "value": round(spct, 2), "threshold": 60.0, "detected_at": datetime.now().isoformat()
                })

    # 3. Large unusual transactions
    if not transactions.empty:
        avg_txn = transactions["amount"].mean()
        std_txn = transactions["amount"].std()
        for _, row in transactions.iterrows():
            if row["amount"] > avg_txn + (3 * std_txn):
                anomalies.append({
                    "client_id": row["client_id"], "ticker": row["ticker"],
                    "anomaly_type": "LARGE_TRANSACTION", "severity": "MEDIUM",
                    "description": f"Transaction of Rs.{row['amount']:,} is {((row['amount']-avg_txn)/std_txn):.1f} std devs above mean.",
                    "value": row["amount"], "threshold": round(avg_txn + 3*std_txn, 2),
                    "detected_at": datetime.now().isoformat()
                })

    # 4. P&L anomaly — extreme losses
    for _, row in portfolios.iterrows():
        loss_pct = (row["unrealized_pnl"] / (row["current_value"] - row["unrealized_pnl"])) * 100 if (row["current_value"] - row["unrealized_pnl"]) != 0 else 0
        if loss_pct < -30:
            anomalies.append({
                "client_id": row["client_id"], "ticker": row["ticker"],
                "anomaly_type": "EXTREME_LOSS", "severity": "HIGH",
                "description": f"{row['ticker']} has {loss_pct:.1f}% unrealized loss — review required.",
                "value": round(loss_pct, 2), "threshold": -30.0, "detected_at": datetime.now().isoformat()
            })

    # 5. Risk profile mismatch
    client_map = clients.set_index("client_id")["risk_appetite"].to_dict()
    AGGRESSIVE_SECTORS = {"Technology", "Automobile", "Consumer Tech"}
    for client_id, group in portfolios.groupby("client_id"):
        risk = client_map.get(client_id, "Moderate")
        if risk == "Conservative":
            total = group["current_value"].sum()
            aggressive_val = group[group["sector"].isin(AGGRESSIVE_SECTORS)]["current_value"].sum()
            agg_pct = aggressive_val / total * 100 if total > 0 else 0
            if agg_pct > 20:
                anomalies.append({
                    "client_id": client_id, "ticker": None,
                    "anomaly_type": "RISK_MISMATCH", "severity": "HIGH",
                    "description": f"Conservative client has {agg_pct:.1f}% in aggressive sectors — suitability breach.",
                    "value": round(agg_pct, 2), "threshold": 20.0, "detected_at": datetime.now().isoformat()
                })

    # Store
    conn = get_db()
    for a in anomalies:
        conn.execute("""
            INSERT INTO anomaly_flags (client_id, ticker, anomaly_type, severity, description, value, threshold, detected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (a["client_id"], a.get("ticker"), a["anomaly_type"], a["severity"],
              a["description"], a["value"], a["threshold"], a["detected_at"]))
    conn.commit()
    conn.close()

    return anomalies

def get_anomalies_for_client(client_id: str) -> List[Dict]:
    conn = get_db()
    df = pd.read_sql("SELECT * FROM anomaly_flags WHERE client_id=? AND resolved=0 ORDER BY detected_at DESC", conn, params=[client_id])
    conn.close()
    return df.to_dict(orient="records")