import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "../data/advisor_ai.db"

def get_db():
    return sqlite3.connect(DB_PATH)

def ensure_graph_tables():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kg_products (
            product_id TEXT PRIMARY KEY, product_name TEXT, category TEXT,
            risk_level TEXT, min_aum REAL, description TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kg_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_type TEXT, from_id TEXT, relationship TEXT,
            to_type TEXT, to_id TEXT, weight REAL DEFAULT 1.0,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kg_client_interests (
            client_id TEXT, product_id TEXT, interest_score REAL,
            last_updated TEXT, PRIMARY KEY (client_id, product_id)
        )
    """)
    existing = conn.execute("SELECT COUNT(*) as c FROM kg_products").fetchone()[0]
    if existing == 0:
        products = [
            ("P001", "Government Bond Fund", "Fixed Income", "Conservative", 100000, "Low risk bond fund"),
            ("P002", "Balanced Mutual Fund", "Hybrid", "Moderate", 200000, "60/40 equity-debt fund"),
            ("P003", "Large Cap Equity Fund", "Equity", "Moderate", 300000, "Blue chip equity fund"),
            ("P004", "Mid Cap Growth Fund", "Equity", "Aggressive", 200000, "High growth mid cap fund"),
            ("P005", "Gold ETF", "Commodity", "Conservative", 50000, "Gold price tracking ETF"),
            ("P006", "Term Life Insurance", "Insurance", "Conservative", 200000, "Pure term insurance"),
            ("P007", "Portfolio Management Service", "Premium", "Moderate", 5000000, "Dedicated PMS"),
            ("P008", "International Equity Fund", "Global", "Aggressive", 500000, "US/Global markets fund"),
            ("P009", "Tax Saver ELSS Fund", "Tax Planning", "Moderate", 50000, "80C tax saving fund"),
            ("P010", "Senior Citizens FD", "Savings", "Conservative", 100000, "High interest FD for seniors"),
        ]
        conn.executemany("INSERT INTO kg_products VALUES (?,?,?,?,?,?)", products)

        relationships = [
            ("RISK_LEVEL", "Conservative", "SUITABLE_FOR", "PRODUCT", "P001", 0.95),
            ("RISK_LEVEL", "Conservative", "SUITABLE_FOR", "PRODUCT", "P005", 0.85),
            ("RISK_LEVEL", "Conservative", "SUITABLE_FOR", "PRODUCT", "P006", 0.90),
            ("RISK_LEVEL", "Conservative", "SUITABLE_FOR", "PRODUCT", "P010", 0.88),
            ("RISK_LEVEL", "Moderate", "SUITABLE_FOR", "PRODUCT", "P002", 0.92),
            ("RISK_LEVEL", "Moderate", "SUITABLE_FOR", "PRODUCT", "P003", 0.88),
            ("RISK_LEVEL", "Moderate", "SUITABLE_FOR", "PRODUCT", "P009", 0.85),
            ("RISK_LEVEL", "Moderate", "SUITABLE_FOR", "PRODUCT", "P007", 0.80),
            ("RISK_LEVEL", "Aggressive", "SUITABLE_FOR", "PRODUCT", "P004", 0.92),
            ("RISK_LEVEL", "Aggressive", "SUITABLE_FOR", "PRODUCT", "P008", 0.88),
            ("GOAL", "Retirement", "RECOMMENDS", "PRODUCT", "P001", 0.90),
            ("GOAL", "Retirement", "RECOMMENDS", "PRODUCT", "P010", 0.85),
            ("GOAL", "Wealth Growth", "RECOMMENDS", "PRODUCT", "P003", 0.88),
            ("GOAL", "Wealth Growth", "RECOMMENDS", "PRODUCT", "P004", 0.85),
            ("GOAL", "Children Education", "RECOMMENDS", "PRODUCT", "P009", 0.90),
            ("GOAL", "Capital Preservation", "RECOMMENDS", "PRODUCT", "P001", 0.95),
        ]
        conn.executemany("""
            INSERT INTO kg_relationships (from_type, from_id, relationship, to_type, to_id, weight, created_at)
            VALUES (?,?,?,?,?,?,?)
        """, [(r[0],r[1],r[2],r[3],r[4],r[5], datetime.now().isoformat()) for r in relationships])

    conn.commit()
    conn.close()

ensure_graph_tables()

def get_product_recommendations_for_client(client_id: str) -> dict:
    conn = get_db()
    client = pd.read_sql("SELECT * FROM clients WHERE client_id=?", conn, params=[client_id])
    if client.empty:
        conn.close()
        return {"error": "Client not found"}
    c = client.iloc[0]

    risk_products = pd.read_sql("""
        SELECT p.*, r.weight as suitability_score FROM kg_products p
        JOIN kg_relationships r ON r.to_id = p.product_id
        WHERE r.from_type='RISK_LEVEL' AND r.from_id=? AND r.relationship='SUITABLE_FOR'
        ORDER BY r.weight DESC
    """, conn, params=[c["risk_appetite"]])

    goal_products = pd.read_sql("""
        SELECT p.*, r.weight as goal_match_score FROM kg_products p
        JOIN kg_relationships r ON r.to_id = p.product_id
        WHERE r.from_type='GOAL' AND r.from_id=? AND r.relationship='RECOMMENDS'
        ORDER BY r.weight DESC
    """, conn, params=[c["investment_goal"]])

    related = pd.read_sql("""
        SELECT DISTINCT p2.product_name, p2.category, p2.risk_level, r2.weight as relevance
        FROM portfolios port
        JOIN kg_relationships r1 ON r1.from_id = port.sector
        JOIN kg_relationships r2 ON r2.from_id = r1.to_id
        JOIN kg_products p2 ON p2.product_id = r2.to_id
        WHERE port.client_id = ?
        LIMIT 5
    """, conn, params=[client_id])

    conn.close()

    return {
        "client_id": client_id,
        "client_name": c["name"],
        "risk_profile": c["risk_appetite"],
        "investment_goal": c["investment_goal"],
        "suitable_products": risk_products[risk_products["min_aum"] <= c["aum"]].to_dict(orient="records"),
        "goal_aligned_products": goal_products.to_dict(orient="records"),
        "graph_insights": f"Knowledge graph identified {len(risk_products)} suitable products for {c['risk_appetite']} profile targeting {c['investment_goal']}."
    }

def get_client_product_network(client_id: str) -> dict:
    conn = get_db()
    client = pd.read_sql("SELECT * FROM clients WHERE client_id=?", conn, params=[client_id])
    holdings = pd.read_sql("SELECT * FROM portfolios WHERE client_id=?", conn, params=[client_id])
    conn.close()

    if client.empty:
        return {}

    c = client.iloc[0]
    nodes = [{"id": client_id, "label": c["name"], "type": "client", "size": 20}]
    edges = []

    for _, h in holdings.iterrows():
        nodes.append({"id": h["ticker"], "label": h["ticker"], "type": "security", "size": 10})
        edges.append({"from": client_id, "to": h["ticker"], "label": "HOLDS", "weight": h["weight_pct"]})

    return {
        "nodes": nodes, "edges": edges,
        "insight": f"{c['name']} holds {len(holdings)} securities across {holdings['sector'].nunique()} sectors."
    }