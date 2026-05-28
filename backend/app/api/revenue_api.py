from fastapi import APIRouter
from pydantic import BaseModel
from app.services.nba_service import get_recommendations, detect_life_events, run_scenario
from app.services.explainability_service import explain_nba_recommendation

router = APIRouter(prefix="/api/revenue", tags=["Revenue & NBA"])

class ScenarioRequest(BaseModel):
    scenario_type: str  # MARKET_CRASH, RATE_HIKE, SECTOR_ROTATION
    magnitude: float    # percentage

@router.get("/nba/{client_id}")
def nba_recommendations(client_id: str):
    recs = get_recommendations(client_id)
    if "recommendations" in recs:
        recs["recommendations"] = [explain_nba_recommendation(r, client_id) for r in recs["recommendations"]]
    return recs

@router.get("/life-events/{client_id}")
def life_events(client_id: str):
    events = detect_life_events(client_id)
    return {"client_id": client_id, "event_count": len(events), "events": events}

@router.post("/scenario/{client_id}")
def scenario_simulation(client_id: str, request: ScenarioRequest):
    return run_scenario(client_id, request.scenario_type, request.magnitude)