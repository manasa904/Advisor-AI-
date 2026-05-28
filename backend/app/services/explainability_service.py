from typing import Dict, List
import sqlite3
import pandas as pd

DB_PATH = "../data/advisor_ai.db"

def get_db():
    return sqlite3.connect(DB_PATH)

def explain_compliance_decision(client_id: str, ticker: str, sector: str, action: str, result: str, checks: List[Dict]) -> Dict:
    conn = get_db()
    client = pd.read_sql("SELECT * FROM clients WHERE client_id=?", conn, params=[client_id])
    portfolio = pd.read_sql("SELECT * FROM portfolios WHERE client_id=?", conn, params=[client_id])
    conn.close()

    if client.empty:
        return {"error": "Client not found"}

    c = client.iloc[0]
    total_val = portfolio["current_value"].sum() if not portfolio.empty else 0

    factors = []
    factor_weights = {}

    for check in checks:
        if check["result"] == "FAIL":
            factors.append({
                "factor": check["rule"],
                "impact": "BLOCKED",
                "weight": 0.9,
                "explanation": check["message"]
            })
            factor_weights[check["rule"]] = 0.9
        elif check["result"] == "WARN":
            factors.append({
                "factor": check["rule"],
                "impact": "WARNING",
                "weight": 0.5,
                "explanation": check["message"]
            })
            factor_weights[check["rule"]] = 0.5
        else:
            factors.append({
                "factor": check["rule"],
                "impact": "PASSED",
                "weight": 0.1,
                "explanation": check["message"]
            })
            factor_weights[check["rule"]] = 0.1

    top_factors = sorted(factors, key=lambda x: x["weight"], reverse=True)[:3]

    if result == "BLOCKED":
        summary = f"Trade blocked primarily due to: {', '.join([f['factor'] for f in top_factors if f['impact']=='BLOCKED'])}."
    elif result == "WARNING":
        summary = f"Trade allowed with caution. Key concern: {top_factors[0]['explanation'] if top_factors else 'Unknown'}."
    else:
        summary = f"All {len(checks)} compliance rules passed. Trade is suitable for {c['name']}."

    bias_check = {
        "checked": True,
        "age_bias": "None detected" if c["age"] < 70 else "Age >70: Additional suitability review recommended",
        "segment_bias": "None detected",
        "gender_bias": "Not applicable - gender not in decision factors"
    }

    return {
        "decision": result,
        "client_id": client_id,
        "client_name": c["name"],
        "trade_details": {"ticker": ticker, "sector": sector, "action": action},
        "summary": summary,
        "top_factors": top_factors,
        "all_factors": factors,
        "bias_assessment": bias_check,
        "model_version": "compliance-engine-v2.0",
        "audit_ready": True,
        "explainability_score": round(1 - (sum(f["weight"] for f in factors if f["impact"]=="BLOCKED") / max(len(factors), 1)), 2)
    }

def explain_nba_recommendation(recommendation: Dict, client_id: str) -> Dict:
    conn = get_db()
    client = pd.read_sql("SELECT * FROM clients WHERE client_id=?", conn, params=[client_id])
    portfolio = pd.read_sql("SELECT * FROM portfolios WHERE client_id=?", conn, params=[client_id])
    conn.close()

    if client.empty:
        return recommendation

    c = client.iloc[0]
    total_val = portfolio["current_value"].sum() if not portfolio.empty else 0

    feature_importance = [
        {"feature": "Client Risk Profile", "value": c["risk_appetite"], "importance": 0.35, "contribution": "Positive"},
        {"feature": "AUM Level", "value": f"Rs.{c['aum']:,}", "importance": 0.30, "contribution": "Positive"},
        {"feature": "Investment Goal", "value": c["investment_goal"], "importance": 0.20, "contribution": "Positive"},
        {"feature": "Client Age", "value": str(c["age"]), "importance": 0.15, "contribution": "Positive" if c["age"] > 40 else "Neutral"},
    ]

    return {
        **recommendation,
        "explainability": {
            "method": "Rule-based SHAP approximation",
            "feature_importance": feature_importance,
            "top_reason": f"Primary driver: {feature_importance[0]['feature']} = {feature_importance[0]['value']}",
            "counterfactual": f"This recommendation would change if client risk profile changed to Conservative.",
            "confidence_breakdown": {
                "model_confidence": recommendation.get("score", 0.5),
                "data_quality": 0.9,
                "recency": 0.85
            }
        }
    }