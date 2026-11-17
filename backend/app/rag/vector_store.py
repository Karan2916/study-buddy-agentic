import logging
import threading
from pathlib import Path
from typing import Any
from uuid import uuid4

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from app.core.config import get_settings
from app.rag.embeddings import get_embeddings
from app.rag.pdf_processor import TextChunk

logger = logging.getLogger(__name__)


class LocalVectorStore:
    def __init__(self, index_dir: Path | None = None):
        self.index_dir = (index_dir or get_settings().index_dir).expanduser().resolve()
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self._store: FAISS | None = None
        self._lock = threading.RLock()

    def _load(self) -> FAISS | None:
        if self._store is not None:
            return self._store
        index_file = self.index_dir / "index.faiss"
        metadata_file = self.index_dir / "index.pkl"
        if index_file.exists() and metadata_file.exists():
            logger.info("Loading FAISS index from %s", self.index_dir)
            try:
                self._store = FAISS.load_local(
                    str(self.index_dir),
                    get_embeddings(),
                    allow_dangerous_deserialization=True,
                )
            except Exception:
                logger.exception("FAISS index load failed; index_dir=%s", self.index_dir)
                raise
        return self._store

    def add_chunks(
        self,
        chunks: list[TextChunk],
        document_id: str,
        document_name: str,
    ) -> int:
        if not chunks:
            return 0
        documents = [
            Document(
                page_content=chunk.text,
                metadata={
                    "document_id": document_id,
                    "document_name": document_name,
                    "page": chunk.page_number,
                },
            )
            for chunk in chunks
        ]
        with self._lock:
            try:
                embedding_model = get_embeddings()
            except Exception:
                logger.exception(
                    "Embedding model initialization failed; document_id=%s "
                    "document_name=%s model=%s",
                    document_id,
                    document_name,
                    get_settings().embedding_model,
                )
                raise
            logger.info(
                "Generating %d embeddings for %s using %s",
                len(documents),
                document_name,
                get_settings().embedding_model,
            )
            try:
                vectors = embedding_model.embed_documents(
                    [document.page_content for document in documents]
                )
            except Exception:
                logger.exception(
                    "Embedding generation failed; document_id=%s document_name=%s "
                    "model=%s chunks=%d",
                    document_id,
                    document_name,
                    get_settings().embedding_model,
                    len(documents),
                )
                raise

            try:
                store = self._load()
            except Exception:
                logger.exception("Could not load existing FAISS index from %s", self.index_dir)
                raise
            text_embeddings = [
                (document.page_content, vector)
                for document, vector in zip(documents, vectors, strict=True)
            ]
            metadatas = [document.metadata for document in documents]
            ids = [str(uuid4()) for _ in documents]
            try:
                if store is None:
                    self._store = FAISS.from_embeddings(
                        text_embeddings,
                        embedding_model,
                        metadatas=metadatas,
                        ids=ids,
                    )
                else:
                    store.add_embeddings(
                        text_embeddings,
                        metadatas=metadatas,
                        ids=ids,
                    )
                    self._store = store
            except Exception:
                logger.exception(
                    "FAISS index update failed; document_id=%s index_dir=%s chunks=%d",
                    document_id,
                    self.index_dir,
                    len(documents),
                )
                raise
            try:
                self._store.save_local(str(self.index_dir))
            except Exception:
                logger.exception(
                    "FAISS persistence failed; document_id=%s index_dir=%s chunks=%d",
                    document_id,
                    self.index_dir,
                    len(documents),
                )
                raise
        return len(documents)

    def search(self, query: str, k: int = 5) -> list[tuple[Document, float]]:
        with self._lock:
            store = self._load()
            if store is None:
                return []
            return store.similarity_search_with_score(query, k=max(1, min(k, 20)))

    def rebuild(self, all_documents: list[dict[str, Any]]) -> None:
        """Re-index saved PDFs after deleting a document."""
        with self._lock:
            self._store = None
            for path in self.index_dir.iterdir():
                if path.is_file() and path.name != ".gitkeep":
                    path.unlink()
            for document in all_documents:
                pdf_path = Path(document["path"])
                if not pdf_path.exists():
                    logger.warning("Skipping missing document file %s", pdf_path)
                    continue
                from app.rag.pdf_processor import chunk_pages, extract_pdf_pages

                chunks = chunk_pages(extract_pdf_pages(pdf_path))
                self.add_chunks(chunks, document["id"], document["name"])

    def remove_document(self, document_id: str) -> None:
        # FAISS does not expose a durable delete operation consistently across
        # supported versions; callers rebuild from the remaining PDF files.
        del document_id


vector_store = LocalVectorStore()


def create_document_id() -> str:
    return str(uuid4())
