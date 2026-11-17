from langgraph.graph import END, StateGraph

from app.agents.research_agent import research
from app.memory.memory_manager import performance_snapshot, record_activity
from app.workflows.graph_state import StudyState


def build_knowledge_gaps_graph():
    graph = StateGraph(StudyState)

    def detect(state: StudyState) -> dict:
        findings = research(
            state.get("request", "Identify topics in uploaded course material."),
            subject=state.get("subject"),
        )
        scores = performance_snapshot()["topic_scores"]
        all_topics = findings.get("topics", [])
        weak = [
            topic for topic in all_topics
            if any(topic.casefold() in known.casefold() or known.casefold() in topic.casefold()
                   for known, score in scores.items() if score < 60)
        ]
        unstudied = [topic for topic in all_topics if topic not in scores]
        recommendations = [
            {"topic": topic, "priority": "high", "reason": "Low quiz performance"}
            for topic in weak
        ] + [
            {"topic": topic, "priority": "medium", "reason": "No quiz history yet"}
            for topic in unstudied
        ]
        result = {
            "topics_in_material": all_topics,
            "topic_scores": scores,
            "weak_topics": weak,
            "unstudied_topics": unstudied,
            "recommendations": recommendations,
            "citations": findings.get("citations", []),
        }
        record_activity("Performance Agent", "completed", "Compared course topics with learning history.")
        return {"gap_analysis": result, "research": findings}

    graph.add_node("detect", detect)
    graph.set_entry_point("detect")
    graph.add_edge("detect", END)
    return graph.compile()


def run_knowledge_gaps(state: StudyState) -> StudyState:
    return build_knowledge_gaps_graph().invoke(state)
