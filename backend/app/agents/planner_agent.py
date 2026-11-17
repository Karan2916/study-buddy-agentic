from datetime import date, timedelta
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.agents.common import invoke_structured
from app.memory.memory_manager import record_activity, record_learning_event, performance_snapshot
from app.storage.json_storage import storage


class PlanSession(BaseModel):
    day: int = Field(ge=1)
    date: str
    focus: str
    tasks: list[str] = Field(default_factory=list)
    duration_hours: float = Field(gt=0)


class StudyPlanDraft(BaseModel):
    title: str
    rationale: str
    sessions: list[PlanSession]


def generate_study_plan(
    subject: str,
    exam_date: date,
    hours_per_day: float,
    topics: list[str],
    *,
    weak_topics: list[str] | None = None,
) -> dict[str, Any]:
    today = date.today()
    days = max(1, (exam_date - today).days)
    if not topics:
        raise ValueError("No topics were found in the uploaded material for this plan.")
    performance = performance_snapshot()
    weaknesses = weak_topics or performance["weak_topics"]
    draft = invoke_structured(
        StudyPlanDraft,
        "You are the Study Planner Agent. Return a practical dated schedule with exactly "
        "one session per study day, from today through the day before the exam (or exam "
        "day only if the exam is today), totaling no more than the available hours each "
        "day. Include revision and active practice. Prioritize weak topics while covering "
        "all topics. Use ISO dates.",
        f"Subject: {subject}\nExam date: {exam_date.isoformat()}\n"
        f"Available hours each day: {hours_per_day}\n"
        f"Topics from course material: {topics}\nWeak topics from performance: {weaknesses}",
    )
    if len(draft.sessions) != days:
        raise RuntimeError(
            f"Study Planner Agent returned {len(draft.sessions)} sessions for {days} study days. "
            "Please try generating the plan again."
        )
    ordered_sessions = sorted(draft.sessions, key=lambda session: session.day)
    sessions = [
        session.model_copy(
            update={
                "day": index + 1,
                "date": (today + timedelta(days=index)).isoformat(),
                "duration_hours": min(session.duration_hours, hours_per_day),
            }
        ).model_dump()
        for index, session in enumerate(ordered_sessions)
    ]
    plan = {
        "id": str(uuid4()),
        "subject": subject,
        "exam_date": exam_date.isoformat(),
        "hours_per_day": hours_per_day,
        "topics": topics,
        "created_at": date.today().isoformat(),
        "title": draft.title,
        "rationale": draft.rationale,
        "sessions": sessions,
    }
    storage.append("study_plans.json", plan)
    record_learning_event("study_plan", subject, f"Created a {days}-day study plan.")
    record_activity("Study Planner Agent", "completed", f"Created a {days}-day schedule.")
    return plan
