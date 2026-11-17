import logging
from datetime import date

from fastapi import APIRouter, HTTPException

from app.api.models import (
    AdaptiveLearningRequest,
    ExamPreparationRequest,
    KnowledgeGapsRequest,
    AdaptiveLearningResponse,
    ExamPreparationResponse,
    KnowledgeGapResponse,
    RevisionKitResponse,
    RevisionKitRequest,
)
from app.memory.memory_manager import record_activity
from app.workflows.adaptive_learning import run_adaptive_learning
from app.workflows.exam_prep import run_exam_prep
from app.workflows.knowledge_gaps import run_knowledge_gaps
from app.workflows.revision_kit import run_revision_kit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/workflows", tags=["workflows"])


def _run(workflow, state: dict):
    try:
        return workflow(state)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422 if isinstance(exc, ValueError) else 503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Workflow execution failed")
        record_activity("Orchestrator Agent", "error", "Workflow execution failed.", str(exc))
        raise HTTPException(status_code=502, detail=f"Workflow execution failed: {exc}") from exc


@router.post("/exam-preparation", response_model=ExamPreparationResponse)
def exam_preparation(request: ExamPreparationRequest):
    if request.exam_date < date.today():
        raise HTTPException(status_code=422, detail="Exam date must be today or in the future.")
    result = _run(
        run_exam_prep,
        {
            "request": f"Prepare me for my {request.subject} exam.",
            "subject": request.subject,
            "exam_date": request.exam_date.isoformat(),
            "hours_per_day": request.hours_per_day,
        },
    )
    return {
        "research": result["research"],
        "plan": result["plan"],
        "explanation": result["explanation"],
        "quiz": result["quiz"],
    }


@router.post("/adaptive-learning", response_model=AdaptiveLearningResponse)
def adaptive_learning(request: AdaptiveLearningRequest):
    result = _run(
        run_adaptive_learning,
        {
            "subject": request.subject,
            "topic": request.topic,
            "mode": request.mode,
            "difficulty": request.difficulty,
            "question_count": request.question_count,
        },
    )
    return {
        "explanation": result["explanation"],
        "quiz": result["quiz"],
        "citations": result["research"]["citations"],
    }


@router.post("/revision-kit", response_model=RevisionKitResponse)
def revision_kit(request: RevisionKitRequest):
    result = _run(
        run_revision_kit,
        {"subject": request.subject, "topic": request.topic},
    )
    return {"kit": result["revision_kit"], "citations": result["research"]["citations"]}


@router.post("/knowledge-gaps", response_model=KnowledgeGapResponse)
def knowledge_gaps(request: KnowledgeGapsRequest):
    result = _run(
        run_knowledge_gaps,
        {
            "subject": request.subject,
            "request": f"Identify all major topics in {request.subject} course material."
            if request.subject
            else "Identify all major topics in uploaded course material.",
        },
    )
    return result["gap_analysis"]
