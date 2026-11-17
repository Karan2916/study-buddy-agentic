from fastapi import APIRouter, Query

from app.api.models import ActivityEventResponse, PerformanceResponse
from app.storage.json_storage import storage

router = APIRouter(prefix="/api", tags=["performance"])


@router.get("/performance", response_model=PerformanceResponse)
def get_performance():
    from app.memory.memory_manager import performance_snapshot

    snapshot = performance_snapshot()
    snapshot["history"] = storage.read("quiz_results.json")
    snapshot["learning_history"] = list(reversed(storage.read("learning_history.json")))[0:20]
    return snapshot


@router.get("/agents/activity", response_model=list[ActivityEventResponse])
def agent_activity(limit: int = Query(default=50, ge=1, le=200)):
    events = storage.read("agent_activity.json")
    return list(reversed(events[-limit:]))
