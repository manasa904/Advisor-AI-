import sqlite3
import json
from datetime import datetime
from typing import Optional
import os

DB_PATH = "../data/advisor_ai.db"

# ── Firm Policy Constants ──────────────────────────────────────────────────
MAX_SECTOR_CONCENTRATION = 40.0   # % max in any single sector
MAX_POSITION_SIZE        = 25.0   # % max in any single holding
MAX_EQUITY_FOR_CONSERVATIVE = 60.0  # % max equity for conservative clients

RESTRICTED_SECURITIES = [
    "GME", "AMC", "BBBY", "SPCE", "DWAC",  # Meme/restricted stocks
]

WATCHLIST_SECURITIES = [
    "ADANI", "PAYTM", "BYJU",  # Under regulatory scrutiny
]

RISK_SUITABILITY = {
    "Conservative": ["Bonds", "Index", "Commodities", "Insurance"],
    "Moderate":     ["Bonds", "Index", "Financials", "Energy", "Consumer", "Commodities"],
    "Aggressive":   ["Technology", "Automobile", "Consumer Tech", "Financials",
                     "Energy", "Consumer", "Bonds", "Index", "Commodities"]
}

# ── DB Setup ───────────────────────────────────────────────────────────────
def get_db():
    return sqlite3.connect(DB_PATH)

def ensure_audit_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS compliance_audit (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            client_id   TEXT NOT NULL,
            rule_name   TEXT NOT NULL,
            ticker      TEXT,
            action      TEXT,
            result      TEXT NOT NULL,
            severity    TEXT NOT NULL,
            message     TEXT NOT NULL,
            details     TEXT
        )
    """)
    conn.commit()
    conn.close()

ensure_audit_table()

# ── Audit Logger ───────────────────────────────────────────────────────────
def log_audit(client_id, rule_name, result, severity, message, ticker=None, action=None, details=None):
    conn = get_db()
    conn.execute("""
        INSERT INTO compliance_audit
        (timestamp, client_id, rule_name, ticker, action, result, severity, message, details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        client_id, rule_name, ticker, action,
        result, severity, message,
        json.dumps(details) if details else None
    ))
    conn.commit()
    conn.close()

# ── Helper: Get Client & Portfolio ─────────────────────────────────────────
def get_client_data(client_id: str):
    conn = get_db()
    import pandas as pd
    client = pd.read_sql(
        "SELECT * FROM clients WHERE client_id = ?", conn, params=[client_id]
    )
    portfolio = pd.read_sql(
        "SELECT * FROM portfolios WHERE client_id = ?", conn, params=[client_id]
    )
    conn.close()
    if client.empty:
        return None, None
    return client.iloc[0].to_dict(), portfolio

# ── RULE 1: Suitability Check ──────────────────────────────────────────────
def check_suitability(client_id: str, ticker: str, sector: str, action: str) -> dict:
    client, _ = get_client_data(client_id)
    if not client:
        return {"rule": "Suitability", "result": "ERROR", "severity": "HIGH", "message": "Client not found"}

    risk = client["risk_appetite"]
    allowed_sectors = RISK_SUITABILITY.get(risk, [])

    if action.upper() == "BUY" and sector not in allowed_sectors:
        msg = (f"VIOLATION: {ticker} ({sector}) is not suitable for {client['name']} "
               f"with {risk} risk appetite. Allowed sectors: {', '.join(allowed_sectors)}.")
        log_audit(client_id, "Suitability", "FAIL", "HIGH", msg, ticker, action,
                  {"risk_appetite": risk, "sector": sector, "allowed_sectors": allowed_sectors})
        return {"rule": "Suitability", "result": "FAIL", "severity": "HIGH", "message": msg}

    msg = f"PASS: {ticker} ({sector}) is suitable for {risk} risk profile."
    log_audit(client_id, "Suitability", "PASS", "INFO", msg, ticker, action)
    return {"rule": "Suitability", "result": "PASS", "severity": "INFO", "message": msg}

# ── RULE 2: Concentration Check ────────────────────────────────────────────
def check_concentration(client_id: str, ticker: str, sector: str, buy_value: float, action: str) -> dict:
    client, portfolio = get_client_data(client_id)
    if client is None:
        return {"rule": "Concentration", "result": "ERROR", "severity": "HIGH", "message": "Client not found"}

    if portfolio.empty:
        return {"rule": "Concentration", "result": "PASS", "severity": "INFO", "message": "No existing portfolio — no concentration risk."}

    total_value = portfolio["current_value"].sum()
    sector_value = portfolio[portfolio["sector"] == sector]["current_value"].sum()

    if action.upper() == "BUY":
        new_sector_value = sector_value + buy_value
        new_total = total_value + buy_value
        new_pct = (new_sector_value / new_total) * 100
    else:
        new_pct = (sector_value / total_value) * 100 if total_value > 0 else 0

    if new_pct > MAX_SECTOR_CONCENTRATION:
        msg = (f"VIOLATION: This trade will push {sector} sector to {new_pct:.1f}% "
               f"of portfolio for {client['name']} — exceeds {MAX_SECTOR_CONCENTRATION}% limit.")
        log_audit(client_id, "Concentration", "FAIL", "HIGH", msg, ticker, action,
                  {"sector": sector, "new_pct": round(new_pct, 2), "limit": MAX_SECTOR_CONCENTRATION})
        return {"rule": "Concentration", "result": "FAIL", "severity": "HIGH", "message": msg,
                "details": {"sector_pct_after_trade": round(new_pct, 2), "limit": MAX_SECTOR_CONCENTRATION}}

    msg = f"PASS: {sector} concentration will be {new_pct:.1f}% — within {MAX_SECTOR_CONCENTRATION}% limit."
    log_audit(client_id, "Concentration", "PASS", "INFO", msg, ticker, action)
    return {"rule": "Concentration", "result": "PASS", "severity": "INFO", "message": msg}

# ── RULE 3: Position Size Check ─────────────────────────────────────────────
def check_position_size(client_id: str, ticker: str, buy_value: float, action: str) -> dict:
    client, portfolio = get_client_data(client_id)
    if client is None:
        return {"rule": "PositionSize", "result": "ERROR", "severity": "HIGH", "message": "Client not found"}

    total_value = portfolio["current_value"].sum() if not portfolio.empty else 0
    existing = portfolio[portfolio["ticker"] == ticker]["current_value"].sum() if not portfolio.empty else 0

    if action.upper() == "BUY":
        new_position = existing + buy_value
        new_total = total_value + buy_value
    else:
        new_position = max(0, existing - buy_value)
        new_total = total_value

    pct = (new_position / new_total * 100) if new_total > 0 else 0

    if pct > MAX_POSITION_SIZE:
        msg = (f"VIOLATION: {ticker} will be {pct:.1f}% of portfolio for {client['name']} "
               f"— exceeds {MAX_POSITION_SIZE}% single position limit.")
        log_audit(client_id, "PositionSize", "FAIL", "MEDIUM", msg, ticker, action,
                  {"position_pct": round(pct, 2), "limit": MAX_POSITION_SIZE})
        return {"rule": "PositionSize", "result": "FAIL", "severity": "MEDIUM", "message": msg}

    msg = f"PASS: {ticker} position will be {pct:.1f}% — within {MAX_POSITION_SIZE}% limit."
    log_audit(client_id, "PositionSize", "PASS", "INFO", msg, ticker, action)
    return {"rule": "PositionSize", "result": "PASS", "severity": "INFO", "message": msg}

# ── RULE 4: Restricted Securities ──────────────────────────────────────────
def check_restricted(client_id: str, ticker: str, action: str) -> dict:
    if ticker.upper() in RESTRICTED_SECURITIES:
        msg = f"VIOLATION: {ticker} is on the firm's restricted securities list. Trade blocked."
        log_audit(client_id, "RestrictedList", "FAIL", "CRITICAL", msg, ticker, action)
        return {"rule": "RestrictedList", "result": "FAIL", "severity": "CRITICAL", "message": msg}

    msg = f"PASS: {ticker} is not on the restricted securities list."
    log_audit(client_id, "RestrictedList", "PASS", "INFO", msg, ticker, action)
    return {"rule": "RestrictedList", "result": "PASS", "severity": "INFO", "message": msg}

# ── RULE 5: Watchlist Screening ────────────────────────────────────────────
def check_watchlist(client_id: str, ticker: str, action: str) -> dict:
    if ticker.upper() in WATCHLIST_SECURITIES:
        msg = f"WARNING: {ticker} is on the compliance watchlist — under regulatory scrutiny. Requires supervisor approval."
        log_audit(client_id, "Watchlist", "WARN", "MEDIUM", msg, ticker, action)
        return {"rule": "Watchlist", "result": "WARN", "severity": "MEDIUM", "message": msg}

    msg = f"PASS: {ticker} is not on the watchlist."
    log_audit(client_id, "Watchlist", "PASS", "INFO", msg, ticker, action)
    return {"rule": "Watchlist", "result": "PASS", "severity": "INFO", "message": msg}

# ── MAIN: Pre-Trade Check ──────────────────────────────────────────────────
def run_pretrade_check(client_id: str, ticker: str, sector: str, action: str, quantity: int, price: float) -> dict:
    buy_value = quantity * price
    checks = [
        check_restricted(client_id, ticker, action),
        check_watchlist(client_id, ticker, action),
        check_suitability(client_id, ticker, sector, action),
        check_concentration(client_id, ticker, sector, buy_value, action),
        check_position_size(client_id, ticker, buy_value, action),
    ]

    violations  = [c for c in checks if c["result"] == "FAIL"]
    warnings    = [c for c in checks if c["result"] == "WARN"]
    passed      = [c for c in checks if c["result"] == "PASS"]

    overall = "BLOCKED" if violations else ("WARNING" if warnings else "APPROVED")

    return {
        "overall_result": overall,
        "client_id":      client_id,
        "ticker":         ticker,
        "action":         action,
        "quantity":       quantity,
        "price":          price,
        "trade_value":    buy_value,
        "timestamp":      datetime.now().isoformat(),
        "summary": {
            "total_checks": len(checks),
            "passed":       len(passed),
            "warnings":     len(warnings),
            "violations":   len(violations)
        },
        "checks": checks
    }

# ── Audit Log Retrieval ─────────────────────────────────────────────────────
def get_audit_log(client_id: Optional[str] = None, limit: int = 50) -> list:
    conn = get_db()
    import pandas as pd
    if client_id:
        df = pd.read_sql(
            "SELECT * FROM compliance_audit WHERE client_id = ? ORDER BY timestamp DESC LIMIT ?",
            conn, params=[client_id, limit]
        )
    else:
        df = pd.read_sql(
            "SELECT * FROM compliance_audit ORDER BY timestamp DESC LIMIT ?",
            conn, params=[limit]
        )
    conn.close()
    return df.to_dict(orient="records")

def get_violations_summary() -> list:
    conn = get_db()
    import pandas as pd
    df = pd.read_sql("""
        SELECT client_id, rule_name, severity, COUNT(*) as count,
               MAX(timestamp) as last_occurrence
        FROM compliance_audit
        WHERE result IN ('FAIL', 'WARN')
        GROUP BY client_id, rule_name, severity
        ORDER BY last_occurrence DESC
    """, conn)
    conn.close()
    return df.to_dict(orient="records")