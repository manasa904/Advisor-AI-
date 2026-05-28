import requests

# Ingest (already done, skip if re-running)
with open("data/unstructured/sample_research.txt", "r", encoding="utf-8") as f:
    text = f.read()

res = requests.post("http://localhost:8000/api/chat/ingest", json={
    "text": text,
    "doc_id": "research_001",
    "doc_type": "research_report"
})
print("INGEST:", res.json())

# Query - with 120 second timeout for first LLM load
print("\nQuerying LLM... (first call may take 30-40 seconds)")
res = requests.post(
    "http://localhost:8000/api/chat/query",
    json={"question": "What is the recommendation for Apple stock?"},
    timeout=120
)
print("QUERY:", res.json())