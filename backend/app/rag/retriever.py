from typing import Any

from app.rag.vector_store import LocalVectorStore, vector_store


def format_citations(results: list[tuple[Any, float]]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for document, _score in results:
        metadata = document.metadata
        key = (str(metadata.get("document_id", "")), int(metadata.get("page", 0)))
        if not key[0] or key in seen:
            continue
        seen.add(key)
        citations.append(
            {
                "document_id": key[0],
                "document_name": metadata.get("document_name", "Unknown document"),
                "page": key[1],
            }
        )
    return citations


class CourseRetriever:
    def __init__(self, store: LocalVectorStore | None = None):
        self.store = store or vector_store

    def search_course_material(self, query: str, k: int = 5) -> dict[str, Any]:
        results = self.store.search(query, k)
        return {
            "chunks": [
                {
                    "text": doc.page_content,
                    "document_name": doc.metadata.get("document_name"),
                    "page": doc.metadata.get("page"),
                    "document_id": doc.metadata.get("document_id"),
                    "score": float(score),
                }
                for doc, score in results
            ],
            "citations": format_citations(results),
        }

    def get_relevant_pages(self, query: str, k: int = 8) -> list[dict[str, Any]]:
        return self.search_course_material(query, k)["citations"]


retriever = CourseRetriever()
