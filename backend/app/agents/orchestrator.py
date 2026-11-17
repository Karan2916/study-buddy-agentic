from typing import Literal
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.agents.common import invoke_structured
from app.memory.memory_manager import record_activity


class RoutingDecision(BaseModel):
    next_agent: Literal["research", "tutor", "quiz", "planner", "performance", "finish"]
    reason: str
    final_answer: str = Field(default="")
    exam_days: Optional[int] = Field(default=None, ge=1, le=365)
    hours_per_day: Optional[float] = Field(default=None, gt=0, le=24)
    subject: Optional[str] = None


def decide_route(
    request: str,
    completed: list[str],
    has_material: bool,
    *,
    today: date | None = None,
) -> RoutingDecision:
    from app.core.config import get_settings
    from app.core.llm import get_llm

    get_settings().validate_llm_settings()
    decision = get_llm().with_structured_output(RoutingDecision).invoke(
        [
            (
                "system",
                "You are the Study Buddy Orchestrator. Delegate only the agents needed "
                "for the current user request, one at a time, then finish. The research "
                "agent must run before tutor/quiz/planner whenever course grounding is "
                "needed. Available agents: research (find course sources/topics), tutor "
                "(explain/answer), quiz (make a quiz), planner (make a schedule), "
                "performance (analyze history). Never route to an already completed agent. "
                "If there is no uploaded material and the request needs grounding, research "
                "once and then finish with an honest limitation. For a broad exam-prep request "
                "with material, research then planner then tutor then quiz. Do not call all "
                "agents for unrelated requests. If creating an exam plan, extract the subject, "
                "days until the exam, and hours per day from the request when present. If not "
                "specified, use 7 days and 2 hours/day and state this assumption in the reason. "
                "The current date is " + (today or date.today()).isoformat() + ".",
            ),
            (
                "human",
                f"Request: {request}\nCompleted agents: {completed}\n"
                f"Uploaded material available: {has_material}",
            ),
        ]
    )
    next_agent = decision.next_agent
    reason = decision.reason
    if next_agent in completed:
        next_agent = "finish"
        reason = "The selected specialist has already completed its task; avoiding duplicate execution."
    elif next_agent in {"tutor", "quiz", "planner"} and "research" not in completed:
        next_agent = "research"
        reason = "Course-grounded work requires Research Agent retrieval first."
    elif not has_material and "research" in completed and next_agent != "finish":
        next_agent = "finish"
        reason = "No matching course excerpts were retrieved; stopping rather than generating unsupported content."
    record_activity(
        "Orchestrator Agent",
        "routing",
        f"Delegating to {next_agent}." if next_agent != "finish" else "Finishing this request.",
        reason,
    )
    decision.next_agent = next_agent
    decision.reason = reason
    return decision


def run_orchestrator(state: dict) -> dict:
    from app.workflows.orchestrator_graph import build_orchestrator_graph

    return build_orchestrator_graph().invoke(state)
