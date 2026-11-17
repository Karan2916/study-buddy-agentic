from datetime import date, timedelta
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.orchestrator import decide_route
from app.agents.performance_agent import analyze
from app.agents.planner_agent import generate_study_plan
from app.agents.quiz_agent import generate_quiz
from app.agents.research_agent import research
from app.agents.tutor_agent import explain
from app.memory.memory_manager import record_activity
from app.rag.retriever import retriever
from app.workflows.graph_state import StudyState


def _context(state: StudyState) -> str:
    research_data = state.get("research", {})
    if research_data.get("chunks"):
        return "\n\n".join(
            f"[{c['document_name']}, page {c['page']}]\n{c['text']}"
            for c in research_data["chunks"]
        )
    found = retriever.search_course_material(
        f"{state.get('subject', '')} {state.get('topic', '')} {state.get('request', '')}"
    )
    return "\n\n".join(
        f"[{c['document_name']}, page {c['page']}]\n{c['text']}"
        for c in found["chunks"]
    )


def build_orchestrator_graph():
    graph = StateGraph(StudyState)

    def orchestrate(state: StudyState) -> dict[str, Any]:
        decision = decide_route(
            state["request"],
            state.get("completed_agents", []),
            bool(state.get("research", {}).get("chunks"))
            or bool(retriever.search_course_material(state["request"], 1)["chunks"]),
        )
        values: dict[str, Any] = {
            "next_agent": decision.next_agent,
            "route_reason": decision.reason,
            "final_response": decision.final_answer,
        }
        if decision.subject and not state.get("subject"):
            values["subject"] = decision.subject
        if decision.next_agent == "planner" and not state.get("exam_date"):
            days = decision.exam_days or 7
            values["exam_date"] = (date.today() + timedelta(days=days)).isoformat()
            values["hours_per_day"] = decision.hours_per_day or 2.0
        return values

    def research_node(state: StudyState) -> dict[str, Any]:
        findings = research(state["request"], subject=state.get("subject"))
        return {"research": findings, "completed_agents": state.get("completed_agents", []) + ["research"]}

    def tutor_node(state: StudyState) -> dict[str, Any]:
        answer = explain(
            state["request"],
            _context(state),
            mode=state.get("mode", "simple"),
        )
        return {"explanation": answer, "completed_agents": state.get("completed_agents", []) + ["tutor"]}

    def quiz_node(state: StudyState) -> dict[str, Any]:
        quiz = generate_quiz(
            state.get("subject", "Study"),
            state.get("topic", ""),
            _context(state),
            difficulty=state.get("difficulty", "medium"),
            count=state.get("question_count", 5),
        )
        return {"quiz": quiz, "completed_agents": state.get("completed_agents", []) + ["quiz"]}

    def planner_node(state: StudyState) -> dict[str, Any]:
        findings = state.get("research", {})
        plan = generate_study_plan(
            state.get("subject", "Study"),
            date.fromisoformat(state["exam_date"]),
            float(state.get("hours_per_day", 2)),
            findings.get("topics") or [state.get("topic", "Course review")],
        )
        return {"plan": plan, "completed_agents": state.get("completed_agents", []) + ["planner"]}

    def performance_node(state: StudyState) -> dict[str, Any]:
        result = state.get("result", {})
        snapshot = analyze(result)
        return {"performance": snapshot, "completed_agents": state.get("completed_agents", []) + ["performance"]}

    def select_next(state: StudyState) -> str:
        return state.get("next_agent", "finish")

    def after_agent(state: StudyState) -> str:
        if len(state.get("completed_agents", [])) >= 5:
            return "finish"
        return "orchestrator"

    def finish(state: StudyState) -> dict[str, Any]:
        outputs = []
        if state.get("research"):
            outputs.append(state["research"].get("summary", ""))
        if state.get("plan"):
            outputs.append("A personalized study plan and diagnostic quiz are ready.")
        if state.get("explanation"):
            outputs.append(state["explanation"])
        if state.get("quiz"):
            outputs.append("A diagnostic quiz is ready in the Quiz Center.")
        if state.get("performance"):
            perf = state["performance"]
            outputs.append(
                f"Your quiz history averages {perf.get('average_score', 0):.0f}%. "
                f"Strong topics: {', '.join(perf.get('strong_topics', [])) or 'not enough data yet'}. "
                f"Topics to revisit: {', '.join(perf.get('weak_topics', [])) or 'none identified'}."
            )
        answer = "\n\n".join(item for item in outputs if item)
        if not answer:
            answer = state.get("final_response") or (
                "I could not ground this request in uploaded course material. "
                "Upload a relevant text-based PDF and try again."
            )
        record_activity("Orchestrator Agent", "completed", "Combined specialist agent outputs.")
        return {"final_response": answer}

    graph.add_node("orchestrator", orchestrate)
    graph.add_node("research", research_node)
    graph.add_node("tutor", tutor_node)
    graph.add_node("quiz", quiz_node)
    graph.add_node("planner", planner_node)
    graph.add_node("performance", performance_node)
    graph.add_node("finish", finish)
    graph.set_entry_point("orchestrator")
    graph.add_conditional_edges(
        "orchestrator",
        select_next,
        {
            "research": "research",
            "tutor": "tutor",
            "quiz": "quiz",
            "planner": "planner",
            "performance": "performance",
            "finish": "finish",
        },
    )
    for name in ("research", "tutor", "quiz", "planner", "performance"):
        graph.add_conditional_edges(name, after_agent, {"orchestrator": "orchestrator", "finish": "finish"})
    graph.add_edge("finish", END)
    return graph.compile()
