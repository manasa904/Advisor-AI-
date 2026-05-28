import sqlite3
import pandas as pd
from datetime import datetime
from typing import Optional

DB_PATH = "../data/advisor_ai.db"

def get_db():
    return sqlite3.connect(DB_PATH)

def ensure_nba_tables():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS nba_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            product TEXT NOT NULL,
            score REAL NOT NULL,
            expected_revenue REAL,
            rationale TEXT NOT NULL,
            urgency TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS life_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            description TEXT NOT NULL,
            detected_at TEXT NOT NULL,
            actioned INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

ensure_nba_tables()

PRODUCTS = {
    "Conservative": [
        {"product": "Government Bond Fund", "category": "Fixed Income", "min_aum": 500000},
        {"product": "Senior Citizens Savings Scheme", "category": "Savings", "min_aum": 100000},
        {"product": "Term Life Insurance", "category": "Insurance", "min_aum": 200000},
        {"product": "Gold ETF", "category": "Commodity", "min_aum": 100000},
    ],
    "Moderate": [
        {"product": "Balanced Mutual Fund", "category": "Hybrid", "min_aum": 200000},
        {"product": "Large Cap Equity Fund", "category": "Equity", "min_aum": 300000},
        {"product": "Corporate Bond Fund", "category": "Fixed Income", "min_aum": 500000},
        {"product": "SIP in Index Fund", "category": "Equity", "min_aum": 100000},
    ],
    "Aggressive": [
        {"product": "Mid Cap Equity Fund", "category": "Equity", "min_aum": 200000},
        {"product": "International ETF", "category": "Global Equity", "min_aum": 500000},
        {"product": "Small Cap Growth Fund", "category": "Equity", "min_aum": 300000},
        {"product": "REIT Fund", "category": "Real Estate", "min_aum": 400000},
    ],
}

def get_recommendations(client_id: str) -> dict:
    conn = get_db()
    client = pd.read_sql("SELECT * FROM clients WHERE client_id=?", conn, params=[client_id])
    portfolio = pd.read_sql("SELECT * FROM portfolios WHERE client_id=?", conn, params=[client_id])
    txns = pd.read_sql("SELECT * FROM transactions WHERE client_id=? ORDER BY txn_date DESC LIMIT 10", conn, params=[client_id])
    conn.close()

    if client.empty:
        return {"error": "Client not found"}

    c = client.iloc[0]
    risk = c["risk_appetite"]
    aum = c["aum"]
    age = c["age"]
    goal = c["investment_goal"]

    total_val = portfolio["current_value"].sum() if not portfolio.empty else 0
    sector_map = portfolio.groupby("sector")["current_value"].sum().to_dict() if not portfolio.empty else {}
    existing_sectors = set(sector_map.keys())
    total_pnl = portfolio["unrealized_pnl"].sum() if not portfolio.empty else 0

    recommendations = []

    # 1. Cross-sell based on missing product categories
    eligible = [p for p in PRODUCTS.get(risk, []) if aum >= p["min_aum"]]
    for p in eligible[:2]:
        score = round(0.5 + (aum / 10000000) * 0.3 + (0.1 if age > 50 else 0), 2)
        score = min(score, 0.95)
        recommendations.append({
            "type": "CROSS_SELL",
            "product": p["product"],
            "category": p["category"],
            "score": score,
            "expected_revenue": round(aum * 0.005, 0),
            "rationale": f"Client has Rs.{aum:,} AUM with {risk} risk profile. {p['product']} aligns with {goal} goal and has not been offered yet.",
            "urgency": "this_month",
            "confidence": f"{int(score*100)}%"
        })

    # 2. Rebalancing opportunity
    if sector_map:
        max_sector = max(sector_map, key=sector_map.get)
        max_pct = sector_map[max_sector] / total_val * 100 if total_val > 0 else 0
        if max_pct > 40:
            recommendations.append({
                "type": "REBALANCE",
                "product": "Portfolio Rebalancing",
                "category": "Advisory",
                "score": 0.88,
                "expected_revenue": round(total_val * 0.003, 0),
                "rationale": f"{max_sector} sector is {max_pct:.1f}% of portfolio — above 40% limit. Recommend reducing and reallocating to diversify.",
                "urgency": "this_week",
                "confidence": "88%"
            })

    # 3. Tax-loss harvesting
    if total_pnl < -50000:
        recommendations.append({
            "type": "TAX_HARVEST",
            "product": "Tax-Loss Harvesting",
            "category": "Tax Planning",
            "score": 0.82,
            "expected_revenue": round(abs(total_pnl) * 0.3 * 0.002, 0),
            "rationale": f"Unrealized loss of Rs.{abs(total_pnl):,.0f} in portfolio. Tax-loss harvesting before year-end could save significant tax.",
            "urgency": "this_week",
            "confidence": "82%"
        })

    # 4. Upsell for high AUM clients
    if aum > 5000000:
        recommendations.append({
            "type": "UPSELL",
            "product": "Portfolio Management Service (PMS)",
            "category": "Premium Advisory",
            "score": 0.79,
            "expected_revenue": round(aum * 0.015, 0),
            "rationale": f"Client AUM of Rs.{aum:,} qualifies for PMS. Dedicated portfolio manager can optimize returns beyond standard advisory.",
            "urgency": "this_month",
            "confidence": "79%"
        })

    # 5. Insurance gap
    if age > 40 and "Insurance" not in existing_sectors:
        recommendations.append({
            "type": "INSURANCE_GAP",
            "product": "Term Life Insurance",
            "category": "Protection",
            "score": 0.75,
            "expected_revenue": round(aum * 0.001, 0),
            "rationale": f"Client aged {age} with Rs.{aum:,} AUM has no insurance coverage in portfolio. Critical protection gap identified.",
            "urgency": "this_month",
            "confidence": "75%"
        })

    # Save to DB
    conn = get_db()
    for r in recommendations:
        conn.execute("""
            INSERT INTO nba_recommendations (client_id, action_type, product, score, expected_revenue, rationale, urgency, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (client_id, r["type"], r["product"], r["score"], r["expected_revenue"], r["rationale"], r["urgency"], datetime.now().isoformat()))
    conn.commit()
    conn.close()

    recommendations.sort(key=lambda x: x["score"], reverse=True)

    return {
        "client_id": client_id,
        "client_name": c["name"],
        "risk_appetite": risk,
        "aum": int(aum),
        "total_recommendations": len(recommendations),
        "total_expected_revenue": int(sum(r["expected_revenue"] for r in recommendations)),
        "recommendations": recommendations
    }

def detect_life_events(client_id: str) -> list:
    conn = get_db()
    client = pd.read_sql("SELECT * FROM clients WHERE client_id=?", conn, params=[client_id])
    portfolio = pd.read_sql("SELECT * FROM portfolios WHERE client_id=?", conn, params=[client_id])
    conn.close()

    if client.empty:
        return []

    c = client.iloc[0]
    events = []

    if c["age"] >= 60:
        events.append({
            "event_type": "RETIREMENT_APPROACHING",
            "description": f"Client {c['name']} is {c['age']} years old — retirement planning and RMD review required.",
            "action": "Review asset allocation for income generation. Consider annuities and systematic withdrawal plan.",
            "urgency": "HIGH"
        })

    if c["age"] >= 58 and c["age"] < 60:
        events.append({
            "event_type": "PRE_RETIREMENT_WINDOW",
            "description": f"Client enters critical pre-retirement window within 2 years.",
            "action": "Begin de-risking portfolio gradually. Shift to capital preservation strategy.",
            "urgency": "MEDIUM"
        })

    if c["investment_goal"] == "Children Education" and c["age"] >= 45:
        events.append({
            "event_type": "EDUCATION_GOAL_DEADLINE",
            "description": f"Education funding goal likely approaching within 3-5 years.",
            "action": "Review education corpus. Ensure adequate liquid funds are available.",
            "urgency": "HIGH"
        })

    if c["aum"] > 8000000:
        events.append({
            "event_type": "WEALTH_MILESTONE",
            "description": f"Client crossed Rs.80L AUM milestone — estate planning recommended.",
            "action": "Introduce trust account, will planning, and wealth transfer solutions.",
            "urgency": "MEDIUM"
        })

    if not portfolio.empty:
        total_val = portfolio["current_value"].sum()
        equity_val = portfolio[portfolio["sector"].isin(["Technology", "Automobile", "Consumer Tech"])]["current_value"].sum()
        equity_pct = equity_val / total_val * 100 if total_val > 0 else 0
        if equity_pct > 70 and c["risk_appetite"] == "Conservative":
            events.append({
                "event_type": "RISK_DRIFT",
                "description": f"Portfolio equity allocation ({equity_pct:.1f}%) has drifted above Conservative profile limits.",
                "action": "Immediate portfolio review required. Reduce equity exposure to match risk profile.",
                "urgency": "HIGH"
            })

    conn = get_db()
    for e in events:
        conn.execute("""
            INSERT INTO life_events (client_id, event_type, description, detected_at)
            VALUES (?, ?, ?, ?)
        """, (client_id, e["event_type"], e["description"], datetime.now().isoformat()))
    conn.commit()
    conn.close()

    return events

def run_scenario(client_id: str, scenario_type: str, magnitude: float) -> dict:
    conn = get_db()
    portfolio = pd.read_sql("SELECT * FROM portfolios WHERE client_id=?", conn, params=[client_id])
    client = pd.read_sql("SELECT * FROM clients WHERE client_id=?", conn, params=[client_id])
    conn.close()

    if portfolio.empty:
        return {"error": "No portfolio data"}

    c = client.iloc[0]
    total_val = portfolio["current_value"].sum()
    results = {}

    if scenario_type == "MARKET_CRASH":
        sector_impacts = {
            "Technology": -magnitude * 1.3, "Automobile": -magnitude * 1.1,
            "Consumer Tech": -magnitude * 1.4, "Financials": -magnitude * 0.9,
            "Energy": -magnitude * 0.8, "Bonds": magnitude * 0.2,
            "Commodities": -magnitude * 0.5, "Index": -magnitude,
            "Consumer": -magnitude * 0.7, "Insurance": -magnitude * 0.4
        }
        new_values = []
        for _, row in portfolio.iterrows():
            impact = sector_impacts.get(row["sector"], -magnitude)
            new_val = row["current_value"] * (1 + impact / 100)
            new_values.append({"ticker": row["ticker"], "sector": row["sector"],
                               "current_value": row["current_value"], "new_value": new_val,
                               "change_pct": impact, "impact_rs": new_val - row["current_value"]})
        new_total = sum(v["new_value"] for v in new_values)
        results = {
            "scenario": f"Market Crash -{magnitude}%",
            "current_portfolio_value": int(total_val),
            "scenario_portfolio_value": int(new_total),
            "total_impact_rs": int(new_total - total_val),
            "total_impact_pct": round((new_total - total_val) / total_val * 100, 2),
            "holdings_impact": new_values,
            "recommendation": f"Worst affected: Technology and Consumer Tech. Consider defensive positions in Bonds and Commodities."
        }

    elif scenario_type == "RATE_HIKE":
        rate_impacts = {"Bonds": -magnitude * 0.8, "Financials": magnitude * 0.5,
                        "Technology": -magnitude * 0.3, "Energy": magnitude * 0.2,
                        "Insurance": -magnitude * 0.1}
        new_values = []
        for _, row in portfolio.iterrows():
            impact = rate_impacts.get(row["sector"], 0)
            new_val = row["current_value"] * (1 + impact / 100)
            new_values.append({"ticker": row["ticker"], "sector": row["sector"],
                               "current_value": row["current_value"], "new_value": new_val,
                               "change_pct": impact, "impact_rs": new_val - row["current_value"]})
        new_total = sum(v["new_value"] for v in new_values)
        results = {
            "scenario": f"Rate Hike +{magnitude}%",
            "current_portfolio_value": int(total_val),
            "scenario_portfolio_value": int(new_total),
            "total_impact_rs": int(new_total - total_val),
            "total_impact_pct": round((new_total - total_val) / total_val * 100, 2),
            "holdings_impact": new_values,
            "recommendation": f"Bond holdings will reprice negatively. Financials may benefit. Review duration exposure."
        }

    elif scenario_type == "SECTOR_ROTATION":
        from_sector = "Technology"
        to_sector = "Financials"
        new_values = []
        for _, row in portfolio.iterrows():
            impact = -magnitude if row["sector"] == from_sector else (magnitude * 1.5 if row["sector"] == to_sector else 0)
            new_val = row["current_value"] * (1 + impact / 100)
            new_values.append({"ticker": row["ticker"], "sector": row["sector"],
                               "current_value": row["current_value"], "new_value": new_val,
                               "change_pct": impact, "impact_rs": new_val - row["current_value"]})
        new_total = sum(v["new_value"] for v in new_values)
        results = {
            "scenario": f"Sector Rotation Tech→Financials ({magnitude}%)",
            "current_portfolio_value": int(total_val),
            "scenario_portfolio_value": int(new_total),
            "total_impact_rs": int(new_total - total_val),
            "total_impact_pct": round((new_total - total_val) / total_val * 100, 2),
            "holdings_impact": new_values,
            "recommendation": "Consider reducing Tech exposure and rotating into Financials ahead of this scenario."
        }

    results["client_id"] = client_id
    results["client_name"] = c["name"]
    return results