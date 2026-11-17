from langgraph.graph import END, StateGraph

from app.agents.quiz_agent import generate_quiz
from app.agents.tutor_agent import explain
from app.memory.memory_manager import record_activity
from app.rag.retriever import retriever
from app.workflows.graph_state import StudyState


def build_adaptive_learning_graph():
    graph = StateGraph(StudyState)

    def tutor_node(state: StudyState) -> dict:
        record_activity("Orchestrator Agent", "routing", "Routing adaptive topic lesson to Tutor Agent.")
        found = retriever.search_course_material(
            f"{state.get('subject', '')} {state.get('topic', '')}"
        )
        if not found["chunks"]:
            raise ValueError(
                "No matching uploaded material was found. Upload a relevant PDF before starting adaptive learning."
            )
        context = "\n\n".join(
            f"[{chunk['document_name']}, page {chunk['page']}]\n{chunk['text']}"
            for chunk in found["chunks"]
        )
        return {
            "research": found,
            "explanation": explain(
                f"Teach me about {state.get('topic') or state.get('subject')}.",
                context,
                mode=state.get("mode", "simple"),
            ),
        }

    def quiz_node(state: StudyState) -> dict:
        record_activity("Orchestrator Agent", "routing", "Routing lesson check to Quiz Agent.")
        context = "\n\n".join(c["text"] for c in state["research"]["chunks"])
        return {
            "quiz": generate_quiz(
                state.get("subject", "Study"),
                state.get("topic", ""),
                context,
                difficulty=state.get("difficulty", "medium"),
                count=state.get("question_count", 5),
            )
        }

    graph.add_node("tutor", tutor_node)
    graph.add_node("quiz", quiz_node)
    graph.set_entry_point("tutor")
    graph.add_edge("tutor", "quiz")
    graph.add_edge("quiz", END)
    return graph.compile()


def run_adaptive_learning(state: StudyState) -> StudyState:
    return build_adaptive_learning_graph().invoke(state)
