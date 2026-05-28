from fastapi import APIRouter
from pydantic import BaseModel
from app.services.governance_service import (
    submit_hitl, review_hitl, get_hitl_queue,
    get_model_registry, get_model_performance,
    save_conversation, get_conversation_history
)

router = APIRouter(prefix="/api/governance", tags=["Governance & HITL"])

class HITLRequest(BaseModel):
    request_type: str
    client_id: str
    advisor_id: str
    details: str

class HITLReview(BaseModel):
    reviewer_id: str
    decision: str  # approved / rejected
    note: str

class ConversationMessage(BaseModel):
    session_id: str
    user_id: str
    role: str
    content: str
    client_context: str = None

@router.post("/hitl/submit")
def submit_for_review(request: HITLRequest):
    return submit_hitl(request.request_type, request.client_id, request.advisor_id, request.details)

@router.post("/hitl/{hitl_id}/review")
def review_request(hitl_id: int, review: HITLReview):
    return review_hitl(hitl_id, review.reviewer_id, review.decision, review.note)

@router.get("/hitl/queue")
def get_queue(status: str = "pending"):
    return {"status": status, "items": get_hitl_queue(status)}

@router.get("/models/registry")
def model_registry():
    return {"models": get_model_registry()}

@router.get("/models/performance")
def model_performance():
    return {"performance": get_model_performance()}

@router.post("/conversation/save")
def save_message(msg: ConversationMessage):
    save_conversation(msg.session_id, msg.user_id, msg.role, msg.content, msg.client_context)
    return {"status": "saved"}

@router.get("/conversation/{session_id}")
def get_history(session_id: str, limit: int = 20):
    history = get_conversation_history(session_id, limit)
    return {"session_id": session_id, "message_count": len(history), "messages": history}