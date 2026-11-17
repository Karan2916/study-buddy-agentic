from fastapi import APIRouter, HTTPException

from app.api.models import ChatRequest, ChatResponse
from app.memory.memory_manager import record_activity
from app.rag.retriever import retriever
from app.storage.json_storage import storage
from app.workflows.orchestrator_graph import build_orchestrator_graph

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    preferences = storage.read("preferences.json")
    preferences["explanation_mode"] = request.mode
    storage.write("preferences.json", preferences)
    try:
        state = build_orchestrator_graph().invoke(
            {
                "request": request.message,
                "subject": request.subject or "",
                "mode": request.mode,
                "completed_agents": [],
                "agent_outputs": {},
            },
            {"recursion_limit": 30},
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        record_activity("Orchestrator Agent", "error", "The requested workflow failed.", str(exc))
        raise HTTPException(status_code=502, detail=f"Study workflow failed: {exc}") from exc
    citations = (state.get("research") or {}).get("citations", [])
    for citation in citations:
        citation["label"] = f"{citation['document_name']} · p. {citation['page']}"
    return {
        "answer": state.get("final_response", ""),
        "agents": [agent.replace("_", " ").title() + " Agent" for agent in state.get("completed_agents", [])],
        "citations": citations,
        "quiz": state.get("quiz"),
        "plan": state.get("plan"),
    }
