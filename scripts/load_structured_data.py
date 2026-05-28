import sqlite3
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions

DATA_DIR   = "data/structured"
CHROMA_DIR = "data/chromadb"
DB_PATH    = "data/advisor_ai.db"

print("Loading CSVs...")
clients      = pd.read_csv(f"{DATA_DIR}/clients.csv")
portfolios   = pd.read_csv(f"{DATA_DIR}/portfolios.csv")
transactions = pd.read_csv(f"{DATA_DIR}/transactions.csv")
print(f"  Clients: {len(clients)} | Portfolios: {len(portfolios)} | Transactions: {len(transactions)}")

print("\nSaving to SQLite...")
conn = sqlite3.connect(DB_PATH)
clients.to_sql("clients",           conn, if_exists="replace", index=False)
portfolios.to_sql("portfolios",     conn, if_exists="replace", index=False)
transactions.to_sql("transactions", conn, if_exists="replace", index=False)
conn.close()
print(f"  Saved to {DB_PATH}")

print("\nBuilding ChromaDB documents...")
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection(
    name="advisor_knowledge",
    embedding_function=embedding_fn
)

docs, ids, metas = [], [], []

for _, r in clients.iterrows():
    text = (
        f"Client Profile: {r['name']} (ID: {r['client_id']}), Age: {r['age']}, "
        f"Segment: {r['segment']}, AUM: {r['aum']:,}, "
        f"Risk Appetite: {r['risk_appetite']}, "
        f"Investment Goal: {r['investment_goal']}, "
        f"Relationship Manager: {r['relationship_manager']}."
    )
    docs.append(text)
    ids.append(f"client_{r['client_id']}")
    metas.append({"type": "client_profile", "client_id": r['client_id']})

for client_id, group in portfolios.groupby("client_id"):
    total_val = group["current_value"].sum()
    total_pnl = group["unrealized_pnl"].sum()
    sector_breakdown = group.groupby("sector")["current_value"].sum()
    sector_text = ", ".join([f"{s}: {v/total_val*100:.1f}%" for s, v in sector_breakdown.items()])
    top3 = group.nlargest(3, "current_value")[["company_name","weight_pct","unrealized_pnl"]]
    holdings_text = "; ".join([
        f"{r['company_name']} ({r['weight_pct']}% weight, P&L: {r['unrealized_pnl']:,})"
        for _, r in top3.iterrows()
    ])
    tech_weight = sector_breakdown.get("Technology", 0) / total_val * 100
    risk_flag = "HIGH CONCENTRATION RISK in Technology sector (>40%)" if tech_weight > 40 else "No major concentration risk"
    text = (
        f"Portfolio Summary for Client {client_id}: "
        f"Total Value: {total_val:,.0f}, Unrealized P&L: {total_pnl:,.0f}. "
        f"Sector Allocation: {sector_text}. "
        f"Top Holdings: {holdings_text}. "
        f"Risk Assessment: {risk_flag}."
    )
    docs.append(text)
    ids.append(f"portfolio_{client_id}")
    metas.append({"type": "portfolio_summary", "client_id": client_id})

for client_id, group in transactions.groupby("client_id"):
    recent = group.sort_values("txn_date", ascending=False).head(5)
    txn_text = "; ".join([
        f"{r['txn_type']} {r['quantity']} shares of {r['ticker']} at {r['price']} on {r['txn_date']}"
        for _, r in recent.iterrows()
    ])
    docs.append(f"Recent Transactions for Client {client_id}: {txn_text}.")
    ids.append(f"transactions_{client_id}")
    metas.append({"type": "transactions", "client_id": client_id})

collection.upsert(documents=docs, ids=ids, metadatas=metas)
print(f"  Stored {len(docs)} documents in ChromaDB")

print("\n✅ Module 4 complete!")
print(f"   SQLite:   {DB_PATH}")
print(f"   ChromaDB: {CHROMA_DIR}")
print(f"   Vectors:  {len(docs)} documents stored")