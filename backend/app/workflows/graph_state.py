from typing import Any, TypedDict


class StudyState(TypedDict, total=False):
    next_agent: str
    route_reason: str
    request: str
    action: str
    subject: str
    topic: str
    context: str
    mode: str
    exam_date: str
    hours_per_day: float
    difficulty: str
    question_count: int
    answers: dict[str, str]
    quiz_id: str
    result: dict[str, Any]
    performance: dict[str, Any]
    research: dict[str, Any]
    explanation: str
    plan: dict[str, Any]
    quiz: dict[str, Any]
    revision_kit: dict[str, Any]
    gap_analysis: dict[str, Any]
    agent_outputs: dict[str, Any]
    pending_agents: list[str]
    completed_agents: list[str]
    events: list[dict[str, Any]]
    final_response: str
    retry_count: int
