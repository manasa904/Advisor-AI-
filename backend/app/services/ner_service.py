import re
from typing import Dict, List

TICKER_PATTERNS = [
    r'\b(AAPL|MSFT|GOOGL|AMZN|META|TSLA|NVDA|JPM|BAC|GS)\b',
    r'\b(HDFCBANK|RELIANCE|TCS|INFY|WIPRO|SBIN|AXISBANK|ICICIBANK|TATAMOTORS|BAJFINANCE)\b',
    r'\b(NIFTYBEES|GOLDBEES|LIQUIDBEES|JUNIORBEES)\b',
    r'\b(ZOMATO|PAYTM|NYKAA|MAPMYINDIA)\b',
]

AMOUNT_PATTERNS = [
    r'Rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:crore|lakh|L|Cr)?',
    r'\$\s*(\d+(?:,\d+)*(?:\.\d+)?)',
    r'(\d+(?:,\d+)*)\s*(?:crore|lakh)',
]

CLIENT_PATTERNS = [
    r'\b(C\d{3})\b',
    r'\b(client\s+\w+)\b',
]

SECTOR_KEYWORDS = {
    "Technology": ["tech", "software", "IT", "digital", "cloud", "AI", "semiconductor"],
    "Financials": ["bank", "finance", "insurance", "NBFC", "lending"],
    "Energy": ["oil", "gas", "energy", "power", "petroleum"],
    "Bonds": ["bond", "debt", "fixed income", "treasury", "gilt"],
    "Commodities": ["gold", "silver", "commodity", "metal"],
}

FINANCIAL_ACTIONS = {
    "buy": "BUY_INTENT", "purchase": "BUY_INTENT", "invest": "BUY_INTENT",
    "sell": "SELL_INTENT", "exit": "SELL_INTENT", "redeem": "SELL_INTENT",
    "rebalance": "REBALANCE_INTENT", "diversify": "REBALANCE_INTENT",
    "risk": "RISK_QUERY", "volatile": "RISK_QUERY", "loss": "RISK_QUERY",
    "performance": "PERFORMANCE_QUERY", "return": "PERFORMANCE_QUERY", "profit": "PERFORMANCE_QUERY",
    "compliance": "COMPLIANCE_QUERY", "violation": "COMPLIANCE_QUERY",
}

def extract_entities(text: str) -> Dict:
    text_lower = text.lower()
    entities = {"tickers": [], "amounts": [], "client_ids": [], "sectors": [], "intents": [], "dates": []}

    for pattern in TICKER_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities["tickers"].extend([m.upper() for m in matches])
    entities["tickers"] = list(set(entities["tickers"]))

    for pattern in AMOUNT_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities["amounts"].extend(matches)

    for pattern in CLIENT_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities["client_ids"].extend([m.upper() if isinstance(m, str) else m[0].upper() for m in matches])
    entities["client_ids"] = list(set(entities["client_ids"]))

    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(kw.lower() in text_lower for kw in keywords):
            entities["sectors"].append(sector)

    for keyword, intent in FINANCIAL_ACTIONS.items():
        if keyword in text_lower:
            entities["intents"].append(intent)
    entities["intents"] = list(set(entities["intents"]))

    date_matches = re.findall(r'\b(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|today|yesterday|this week|this month)\b', text_lower)
    entities["dates"].extend(date_matches)

    entities["primary_intent"] = entities["intents"][0] if entities["intents"] else "GENERAL_QUERY"
    entities["entity_count"] = sum(len(v) for v in entities.values() if isinstance(v, list))
    return entities

def enrich_query_with_entities(query: str, entities: Dict) -> str:
    enriched = query
    if entities["tickers"]:
        enriched += f" [Tickers detected: {', '.join(entities['tickers'])}]"
    if entities["client_ids"]:
        enriched += f" [Client IDs: {', '.join(entities['client_ids'])}]"
    if entities["primary_intent"] != "GENERAL_QUERY":
        enriched += f" [Intent: {entities['primary_intent']}]"
    return enriched