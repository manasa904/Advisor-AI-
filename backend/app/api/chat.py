from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.rag_service import query_rag, ingest_document

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class QueryRequest(BaseModel):
    question: str

class IngestRequest(BaseModel):
    text: str
    doc_id: str
    doc_type: str = "research_report"

@router.post("/query")
def chat_query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    answer = query_rag(request.question)
    return {"question": request.question, "answer": answer}

@router.post("/ingest")
def ingest(request: IngestRequest):
    result = ingest_document(
        text=request.text,
        doc_id=request.doc_id,
        metadata={"doc_type": request.doc_type}
    )
    return {"status": "success", **result}