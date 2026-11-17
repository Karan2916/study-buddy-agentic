import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.models import DocumentResponse
from app.core.config import get_settings
from app.rag.pdf_processor import chunk_pages, extract_pdf_pages
from app.rag.vector_store import vector_store
from app.storage.json_storage import storage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


def _public_document(document: dict) -> dict:
    return {key: value for key, value in document.items() if key != "path"}


@router.post("/upload", status_code=201, response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    filename = Path(file.filename or "upload.pdf").name
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF documents are supported.")
    content = await file.read(30 * 1024 * 1024 + 1)
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")
    if len(content) > 30 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="PDF exceeds the 30 MB upload limit.")
    settings = get_settings()
    documents_dir = settings.documents_dir.expanduser().resolve()
    document_id = str(uuid4())
    target = documents_dir / f"{document_id}.pdf"
    documents = storage.read("documents.json")
    stage = "create document storage directory"
    try:
        documents_dir.mkdir(parents=True, exist_ok=True)
        if target.parent != documents_dir:
            raise ValueError(f"Resolved PDF path is outside document storage: {target}")
        logger.info("Saving uploaded PDF to %s", target)
        stage = "write uploaded PDF"
        target.write_bytes(content)
        stage = "extract PDF text"
        pages = extract_pdf_pages(target)
        logger.info("Extracted %d page(s) from %s", len(pages), target)
        stage = "chunk extracted PDF text"
        chunks = chunk_pages(pages)
        logger.info("Created %d text chunk(s) from %s", len(chunks), target)
        stage = "embed chunks and update FAISS index"
        indexed_count = vector_store.add_chunks(chunks, document_id, filename)
        if indexed_count != len(chunks):
            raise RuntimeError(
                f"FAISS reported {indexed_count} indexed chunks; expected {len(chunks)}."
            )
        document = {
            "id": document_id,
            "name": filename,
            "pages": len(pages),
            "chunks": indexed_count,
            "size_bytes": len(content),
            "status": "ready",
            "path": str(target),
        }
        documents.append(document)
        stage = "persist document metadata"
        storage.write("documents.json", documents)
    except ValueError as exc:
        logger.exception("PDF upload failed during %s; file=%s", stage, target)
        target.unlink(missing_ok=True)
        try:
            vector_store.rebuild(documents)
        except Exception:
            logger.exception("Could not rebuild FAISS after upload failed during %s", stage)
        raise HTTPException(
            status_code=422,
            detail=f"PDF upload failed during {stage}: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("PDF upload failed during %s; file=%s", stage, target)
        target.unlink(missing_ok=True)
        try:
            vector_store.rebuild(documents)
        except Exception:
            logger.exception("Could not rebuild FAISS after upload failed during %s", stage)
        raise HTTPException(
            status_code=503,
            detail=f"PDF upload failed during {stage}: {type(exc).__name__}: {exc}",
        ) from exc
    return _public_document(document)


@router.get("", response_model=list[DocumentResponse])
def list_documents():
    documents = storage.read("documents.json")
    return [_public_document(document) for document in documents]


@router.delete("/{document_id}")
def delete_document(document_id: str):
    documents = storage.read("documents.json")
    found = next((item for item in documents if item["id"] == document_id), None)
    if not found:
        raise HTTPException(status_code=404, detail="Document not found.")
    settings = get_settings()
    file_path = Path(found["path"]).resolve()
    if file_path.parent != settings.documents_dir.resolve():
        raise HTTPException(status_code=400, detail="Stored document path is outside document storage.")
    file_path.unlink(missing_ok=True)
    remaining = [item for item in documents if item["id"] != document_id]
    storage.write("documents.json", remaining)
    try:
        vector_store.rebuild(remaining)
    except Exception as exc:
        logger.exception("Could not rebuild FAISS index after document removal")
        raise HTTPException(
            status_code=503,
            detail=f"Document was removed, but the local search index could not be rebuilt: {exc}",
        ) from exc
    return {"deleted": document_id}
