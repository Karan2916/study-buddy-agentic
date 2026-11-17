from datetime import date, timedelta

import pytest
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document

from app.agents import planner_agent, quiz_agent, research_agent
from app.agents.orchestrator import RoutingDecision
from app.core.config import Settings
from app.rag import pdf_processor
from app.rag.pdf_processor import PageText, chunk_pages
from app.rag.retriever import CourseRetriever, format_citations
from app.rag.vector_store import LocalVectorStore
from app.storage.json_storage import JsonStorage
from app.tools import learning_tools
from app.workflows import orchestrator_graph


class TinyEmbeddings(Embeddings):
    """Deterministic fixture embeddings; production uses the configured local model."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        terms = text.casefold()
        return [
            float(terms.count("database")),
            float(terms.count("normalization")),
            float(terms.count("transaction")),
            float(terms.count("index")),
        ]


def test_pdf_extraction_preserves_one_based_page_numbers(tmp_path, monkeypatch):
    class FakePage:
        def __init__(self, value):
            self.value = value

        def extract_text(self):
            return self.value

    class FakeReader:
        is_encrypted = False
        pages = [FakePage(" First page "), FakePage("Second page")]

    path = tmp_path / "course.pdf"
    path.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(pdf_processor, "PdfReader", lambda _path: FakeReader())
    assert pdf_processor.extract_pdf_pages(path) == [
        PageText(1, "First page"),
        PageText(2, "Second page"),
    ]


def test_text_chunking_overlaps_without_losing_page_metadata():
    chunks = chunk_pages([PageText(4, "abcdefghij")], chunk_size=6, overlap=2)
    assert [chunk.text for chunk in chunks] == ["abcdef", "efghij"]
    assert [chunk.page_number for chunk in chunks] == [4, 4]
    with pytest.raises(ValueError):
        chunk_pages([], chunk_size=5, overlap=5)


def test_faiss_retrieval_and_page_citations(tmp_path, monkeypatch):
    import app.rag.vector_store as vector_module

    monkeypatch.setattr(vector_module, "get_embeddings", lambda: TinyEmbeddings())
    store = LocalVectorStore(tmp_path / "index")
    store.add_chunks(
        [
            pdf_processor.TextChunk("Database normalization reduces redundancy.", 2),
            pdf_processor.TextChunk("Transactions provide atomicity.", 7),
        ],
        "doc-1",
        "dbms.pdf",
    )
    retriever = CourseRetriever(store)
    result = retriever.search_course_material("database normalization", k=1)
    assert result["chunks"][0]["page"] == 2
    assert result["citations"] == [
        {"document_id": "doc-1", "document_name": "dbms.pdf", "page": 2}
    ]
    reloaded = LocalVectorStore(tmp_path / "index")
    monkeypatch.setattr(vector_module, "get_embeddings", lambda: TinyEmbeddings())
    assert CourseRetriever(reloaded).search_course_material("transaction")["chunks"]


def test_citation_generation_deduplicates_document_and_page():
    first = Document(page_content="one", metadata={"document_id": "a", "document_name": "x.pdf", "page": 1})
    duplicate = Document(page_content="two", metadata={"document_id": "a", "document_name": "x.pdf", "page": 1})
    second = Document(page_content="three", metadata={"document_id": "a", "document_name": "x.pdf", "page": 2})
    citations = format_citations([(first, 0.1), (duplicate, 0.2), (second, 0.3)])
    assert [item["page"] for item in citations] == [1, 2]


def test_research_agent_invokes_local_learning_tools(tmp_path, monkeypatch):
    memory = JsonStorage(tmp_path / "memory")
    memory.write(
        "documents.json",
        [{"id": "doc-1", "name": "dbms.pdf", "path": "local-only"}],
    )
    monkeypatch.setattr(learning_tools, "storage", memory)
    monkeypatch.setattr(
        learning_tools.retriever,
        "search_course_material",
        lambda query, k: {"chunks": [], "citations": []},
    )
    assert research_agent.get_document_information() == [{"id": "doc-1", "name": "dbms.pdf"}]
    assert research_agent.search_course_material("DBMS", 2) == {"chunks": [], "citations": []}


def test_orchestrator_routes_only_selected_agents(tmp_path, monkeypatch):
    decisions = [
        RoutingDecision(next_agent="research", reason="Need sources"),
        RoutingDecision(next_agent="tutor", reason="Explain requested concept"),
        RoutingDecision(next_agent="finish", reason="Request answered"),
    ]
    called = []
    monkeypatch.setattr(orchestrator_graph, "decide_route", lambda *_args, **_kwargs: decisions.pop(0))
    monkeypatch.setattr(
        orchestrator_graph.retriever,
        "search_course_material",
        lambda *_args, **_kwargs: {"chunks": [{"text": "source", "document_name": "dbms.pdf", "page": 1}], "citations": []},
    )
    monkeypatch.setattr(
        orchestrator_graph,
        "research",
        lambda *_args, **_kwargs: {"topics": ["Database"], "summary": "Database overview.", "chunks": [], "citations": []},
    )
    monkeypatch.setattr(orchestrator_graph, "explain", lambda *_args, **_kwargs: "A grounded explanation.")
    monkeypatch.setattr(orchestrator_graph, "generate_quiz", lambda *_args, **_kwargs: pytest.fail("Quiz should not be routed"))
    monkeypatch.setattr(orchestrator_graph, "generate_study_plan", lambda *_args, **_kwargs: pytest.fail("Planner should not be routed"))
    monkeypatch.setattr(orchestrator_graph, "record_activity", lambda *args, **kwargs: called.append(args[0]))
    result = orchestrator_graph.build_orchestrator_graph().invoke(
        {"request": "Explain database normalization", "completed_agents": []},
        {"recursion_limit": 15},
    )
    assert result["completed_agents"] == ["research", "tutor"]
    assert "A grounded explanation." in result["final_response"]
    assert called[-1] == "Orchestrator Agent"


def test_quiz_scoring_and_single_submission(tmp_path, monkeypatch):
    memory = JsonStorage(tmp_path / "memory")
    monkeypatch.setattr(quiz_agent, "storage", memory)
    monkeypatch.setattr(quiz_agent, "record_activity", lambda *args, **kwargs: None)
    memory.write(
        "quizzes.json",
        {
            "quiz-1": {
                "id": "quiz-1",
                "subject": "DBMS",
                "topic": "Transactions",
                "questions": [
                    {"correct_answer": "Atomicity", "explanation": "All or nothing.", "topic": "ACID"},
                    {"correct_answer": "Isolation", "explanation": "Concurrent safety.", "topic": "ACID"},
                ],
            }
        },
    )
    result = quiz_agent.evaluate_quiz("quiz-1", {"0": "atomicity", "1": "wrong"})
    assert (result["score"], result["total"], result["score_percent"]) == (1, 2, 50)
    assert result["topic_scores"] == {"ACID": 50}
    assert len(memory.read("quiz_results.json")) == 1
    with pytest.raises(ValueError, match="already been submitted"):
        quiz_agent.evaluate_quiz("quiz-1", {})


def test_generated_quiz_hides_answers_until_submission(tmp_path, monkeypatch):
    memory = JsonStorage(tmp_path / "memory")
    monkeypatch.setattr(quiz_agent, "storage", memory)
    monkeypatch.setattr(quiz_agent, "record_activity", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        quiz_agent,
        "invoke_structured",
        lambda *_args: quiz_agent.QuizDraft(
            title="Normalization check",
            questions=[
                quiz_agent.QuizQuestion(
                    prompt="Which form removes partial dependency?",
                    options=["1NF", "2NF", "3NF", "BCNF"],
                    correct_answer="2NF",
                    explanation="2NF removes partial dependencies on a composite key.",
                    topic="Normalization",
                ),
                quiz_agent.QuizQuestion(
                    prompt="Which dependency does 3NF address?",
                    options=["Partial", "Transitive", "Multivalued", "Join"],
                    correct_answer="Transitive",
                    explanation="3NF removes transitive dependencies.",
                    topic="Normalization",
                ),
            ],
        ),
    )
    quiz = quiz_agent.generate_quiz("DBMS", "Normalization", "Course excerpts.", count=2)
    assert len(quiz["questions"]) == 2
    assert all("correct_answer" not in question for question in quiz["questions"])
    assert memory.read("quizzes.json")[quiz["id"]]["questions"][0]["correct_answer"] == "2NF"


def test_json_memory_defaults_and_persists_atomically(tmp_path):
    memory = JsonStorage(tmp_path)
    assert memory.read("quiz_results.json") == []
    memory.append("quiz_results.json", {"score_percent": 80})
    assert JsonStorage(tmp_path).read("quiz_results.json") == [{"score_percent": 80}]
    (tmp_path / "preferences.json").write_text("{broken", encoding="utf-8")
    assert memory.read("preferences.json") == {"explanation_mode": "simple"}


def test_study_plan_generation_saves_persistent_plan(tmp_path, monkeypatch):
    memory = JsonStorage(tmp_path / "memory")
    monkeypatch.setattr(planner_agent, "storage", memory)
    monkeypatch.setattr(planner_agent, "record_learning_event", lambda *args: None)
    monkeypatch.setattr(planner_agent, "record_activity", lambda *args: None)
    monkeypatch.setattr(planner_agent, "performance_snapshot", lambda: {"weak_topics": []})
    due = date.today() + timedelta(days=1)
    monkeypatch.setattr(
        planner_agent,
        "invoke_structured",
        lambda *_args: planner_agent.StudyPlanDraft(
            title="DBMS sprint",
            rationale="Focus on fundamentals, then practice.",
            sessions=[
                planner_agent.PlanSession(
                    day=1,
                    date=date.today().isoformat(),
                    focus="Relational model",
                    tasks=["Review keys"],
                    duration_hours=2,
                )
            ],
        ),
    )
    plan = planner_agent.generate_study_plan("DBMS", due, 2, ["Keys", "Normalization"])
    assert plan["subject"] == "DBMS"
    assert plan["sessions"][0]["focus"] == "Relational model"
    assert memory.read("study_plans.json")[0]["id"] == plan["id"]


def test_missing_api_settings_report_exact_configuration_keys():
    settings = Settings(OPENAI_API_KEY="", OPENAI_BASE_URL="", OPENAI_MODEL="")
    assert settings.missing_llm_settings() == [
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_MODEL",
    ]
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        settings.validate_llm_settings()
    placeholder = Settings(
        OPENAI_API_KEY="PASTE_YOUR_API_KEY_HERE",
        OPENAI_BASE_URL="PASTE_YOUR_API_ENDPOINT_HERE",
        OPENAI_MODEL="PASTE_YOUR_DEPLOYMENT_NAME_HERE",
    )
    assert placeholder.missing_llm_settings() == [
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_MODEL",
    ]
