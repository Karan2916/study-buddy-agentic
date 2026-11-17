from datetime import date

from langgraph.graph import END, StateGraph

from app.agents.planner_agent import generate_study_plan
from app.agents.quiz_agent import generate_quiz
from app.agents.research_agent import research
from app.agents.tutor_agent import explain
from app.memory.memory_manager import record_activity
from app.workflows.graph_state import StudyState


def build_exam_prep_graph():
    graph = StateGraph(StudyState)

    def orchestrator_node(state: StudyState) -> dict:
        record_activity(
            "Orchestrator Agent",
            "routing",
            "Exam-preparation request accepted; coordinating research, planning, tutoring, and diagnostics.",
            f"Subject: {state['subject']}; exam date: {state['exam_date']}; "
            f"available time: {state['hours_per_day']} hours/day.",
        )
        return {}

    def research_node(state: StudyState) -> dict:
        findings = research(state["request"], subject=state["subject"])
        if not findings["topics"]:
            raise ValueError("No matching course material was found to prepare this plan.")
        return {"research": findings}

    def planner_node(state: StudyState) -> dict:
        plan = generate_study_plan(
            state["subject"],
            date.fromisoformat(state["exam_date"]),
            float(state["hours_per_day"]),
            state["research"]["topics"],
        )
        return {"plan": plan}

    def tutor_node(state: StudyState) -> dict:
        context = "\n\n".join(c["text"] for c in state["research"]["chunks"])
        explanation = explain(
            f"Identify and briefly explain the most challenging concepts for the "
            f"{state['subject']} exam.",
            context,
            mode="exam",
        )
        return {"explanation": explanation}

    def quiz_node(state: StudyState) -> dict:
        context = "\n\n".join(c["text"] for c in state["research"]["chunks"])
        quiz = generate_quiz(
            state["subject"],
            ", ".join(state["research"]["topics"]),
            context,
            difficulty="medium",
            count=5,
        )
        return {"quiz": quiz}

    def route_to(agent: str):
        def route(_state: StudyState) -> str:
            record_activity("Orchestrator Agent", "routing", f"Delegating to {agent.title()} Agent.")
            return agent

        return route

    graph.add_node("research", research_node)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("planner", planner_node)
    graph.add_node("tutor", tutor_node)
    graph.add_node("quiz", quiz_node)
    graph.set_entry_point("orchestrator")
    graph.add_conditional_edges("orchestrator", route_to("research"), {"research": "research"})
    graph.add_conditional_edges("research", route_to("planner"), {"planner": "planner"})
    graph.add_conditional_edges("planner", route_to("tutor"), {"tutor": "tutor"})
    graph.add_conditional_edges("tutor", route_to("quiz"), {"quiz": "quiz"})
    graph.add_edge("quiz", END)
    return graph.compile()


def run_exam_prep(state: StudyState) -> StudyState:
    return build_exam_prep_graph().invoke(state)
