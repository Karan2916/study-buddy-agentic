from datetime import date

from fastapi import APIRouter, HTTPException

from app.agents.planner_agent import generate_study_plan
from app.agents.research_agent import research
from app.api.models import (
    GeneratedStudyPlanResponse,
    PerformanceResponse,
    StudyPlanEnvelope,
    StudyPlanRequest,
)
from app.memory.memory_manager import performance_snapshot
from app.storage.json_storage import storage

router = APIRouter(prefix="/api/study-plan", tags=["study plans"])


@router.post("/generate", response_model=GeneratedStudyPlanResponse)
def create_study_plan(request: StudyPlanRequest):
    if request.exam_date < date.today():
        raise HTTPException(status_code=422, detail="Exam date must be today or in the future.")
    try:
        findings = research(
            f"Prepare for {request.subject} exam on {request.exam_date.isoformat()}",
            subject=request.subject,
        )
        if not findings["topics"]:
            raise HTTPException(
                status_code=422,
                detail="No matching course topics found. Upload a relevant PDF first.",
            )
        plan = generate_study_plan(
            request.subject,
            request.exam_date,
            request.hours_per_day,
            findings["topics"],
        )
    except HTTPException:
        raise
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"plan": plan, "topics": findings["topics"], "citations": findings["citations"]}


@router.get("", response_model=StudyPlanEnvelope)
def current_study_plan():
    plans = storage.read("study_plans.json")
    return {"current": plans[-1] if plans else None, "history": list(reversed(plans))}


@router.get("/performance", response_model=PerformanceResponse)
def performance():
    return performance_snapshot()
