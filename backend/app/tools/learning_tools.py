from typing import Any

from langchain_core.tools import tool

from app.rag.retriever import retriever
from app.storage.json_storage import storage


@tool
def search_course_material(query: str, k: int = 6) -> dict[str, Any]:
    """Search the locally indexed course PDFs and return source passages and citations."""
    return retriever.search_course_material(query, k)


@tool
def get_document_information() -> list[dict[str, Any]]:
    """List uploaded PDFs and their indexing status without exposing local file paths."""
    documents = storage.read("documents.json")
    if not isinstance(documents, list):
        return []
    return [
        {key: value for key, value in document.items() if key != "path"}
        for document in documents
    ]


@tool
def get_relevant_pages(query: str) -> list[dict[str, Any]]:
    """Find document names and page numbers relevant to a course-material query."""
    return retriever.get_relevant_pages(query)
