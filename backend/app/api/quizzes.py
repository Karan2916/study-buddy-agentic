import logging
from datetime import date

from fastapi import APIRouter, HTTPException

from app.agents.performance_agent import analyze
from app.agents.planner_agent import generate_study_plan
from app.agents.quiz_agent import evaluate_quiz, generate_quiz
from app.api.models import QuizGenerateRequest, QuizResponse, QuizResultResponse, QuizSubmitRequest
from app.memory.memory_manager import record_learning_event
from app.rag.retriever import retriever
from app.storage.json_storage import storage
from app.workflows.adaptive_learning import run_adaptive_learning

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/quiz", tags=["quizzes"])


@router.post("/generate", response_model=QuizResponse)
def create_quiz(request: QuizGenerateRequest):
    found = retriever.search_course_material(
        f"{request.subject} {request.topic}", k=10
    )
    context = "\n\n".join(
        f"[{chunk['document_name']}, page {chunk['page']}]\n{chunk['text']}"
        for chunk in found["chunks"]
    )
    try:
        quiz = generate_quiz(
            request.subject,
            request.topic,
            context,
            difficulty=request.difficulty,
            count=request.question_count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    quiz["citations"] = found["citations"]
    return quiz


@router.post("/submit", response_model=QuizResultResponse)
def submit_quiz(request: QuizSubmitRequest):
    try:
        result = evaluate_quiz(request.quiz_id, request.answers)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    performance = analyze(result)
    result["performance"] = performance
    record_learning_event(
        "quiz",
        result["subject"],
        f"Scored {result['score_percent']}% on quiz {request.quiz_id}.",
    )

    quizzes = storage.read("quizzes.json")
    source_quiz = quizzes.get(request.quiz_id, {})
    retry_quiz = None
    adaptive_explanation = None
    if result["score_percent"] < 60 and source_quiz.get("retry_count", 0) < 2:
        try:
            next_retry_count = source_quiz.get("retry_count", 0) + 1
            adapted = run_adaptive_learning(
                {
                    "subject": result["subject"],
                    "topic": source_quiz.get("topic", ""),
                    "mode": "detailed",
                    "difficulty": source_quiz.get("difficulty", "medium"),
                    "question_count": len(source_quiz.get("questions", [])) or 5,
                    "retry_count": next_retry_count,
                }
            )
            retry_quiz = adapted["quiz"]
            adaptive_explanation = adapted["explanation"]
            quizzes = storage.read("quizzes.json")
            retry_quiz_record = quizzes.get(retry_quiz["id"])
            if retry_quiz_record is not None:
                retry_quiz_record["retry_count"] = next_retry_count
                quizzes[retry_quiz["id"]] = retry_quiz_record
            storage.write("quizzes.json", quizzes)
        except Exception as exc:
            logger.exception("Adaptive follow-up generation failed")
            result["adaptive_error"] = (
                "Your score was saved, but an adaptive explanation and retry could not be generated: "
                f"{exc}"
            )
    result["adaptive_explanation"] = adaptive_explanation
    result["retry_quiz"] = retry_quiz
    result["updated_plan"] = None
    if result["score_percent"] < 60:
        plans = storage.read("study_plans.json")
        current_plan = plans[-1] if plans else None
        if (
            current_plan
            and current_plan.get("exam_date")
            and current_plan["exam_date"] >= date.today().isoformat()
            and current_plan.get("topics")
        ):
            try:
                updated_plan = generate_study_plan(
                    current_plan["subject"],
                    date.fromisoformat(current_plan["exam_date"]),
                    float(current_plan["hours_per_day"]),
                    current_plan["topics"],
                    weak_topics=[
                        topic for topic, score in result["topic_scores"].items() if score < 60
                    ],
                )
                updated_plan["adapted_from_quiz_id"] = request.quiz_id
                result["updated_plan"] = updated_plan
            except Exception as exc:
                logger.exception("Could not adapt the saved study plan")
                result["plan_adaptation_error"] = (
                    "Your result was saved, but the study plan could not be adapted: "
                    f"{exc}"
                )
    return result


@router.get("/history", response_model=list[QuizResultResponse])
def quiz_history():
    return storage.read("quiz_results.json")
