r"""Standalone real-model and PDF-upload smoke test for Windows.

Run from the project root:
    .\backend\venv\Scripts\python.exe .\backend\tests\test_embedding_pipeline.py

Uses the configured sentence-transformers model (no mock embeddings), tests PDF
extraction/chunking and FAISS persistence, then calls the real upload API and
removes the smoke-test document after verification.
"""

import logging
import sys
import tempfile
import traceback
from pathlib import Path

import faiss
import sentence_transformers
import torch
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.main import app
from app.rag.embeddings import get_embeddings
from app.rag.pdf_processor import chunk_pages, extract_pdf_pages
from app.rag.vector_store import LocalVectorStore, vector_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("embedding_pipeline_test")


def make_text_pdf(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 50 750 Td ({escaped}) Tj ET\n".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
        + stream + b"endstream",
    ]
    data = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(data))
        data.extend(f"{number} 0 obj\n".encode("ascii"))
        data.extend(body)
        data.extend(b"\nendobj\n")
    xref_offset = len(data)
    data.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    data.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    data.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(data)


def run_stage(label: str, action):
    logger.info("Starting stage: %s", label)
    try:
        result = action()
    except Exception:
        logger.exception("Stage failed: %s", label)
        raise
    logger.info("Stage passed: %s", label)
    return result


def main() -> int:
    settings = get_settings()
    model_name = settings.embedding_model
    logger.info(
        "Runtime versions: Python %s; PyTorch %s; sentence-transformers %s; FAISS %s",
        sys.version.split()[0],
        torch.__version__,
        sentence_transformers.__version__,
        getattr(faiss, "__version__", "unknown"),
    )
    logger.info(
        "Resolved project paths: documents=%s; FAISS=%s; memory=%s; model cache=%s",
        settings.documents_dir.resolve(),
        settings.index_dir.resolve(),
        settings.memory_dir.resolve(),
        (Path.home() / ".cache" / "huggingface").resolve(),
    )
    content = make_text_pdf(
        "Database management systems organize and protect data. "
        "Normalization reduces duplicate data in relational databases."
    )

    try:
        with tempfile.TemporaryDirectory(prefix="study-buddy-embedding-test-") as temp_name:
            temp_root = Path(temp_name).resolve()
            test_pdf = temp_root / "dbms-embedding-smoke-test.pdf"
            run_stage("write standalone PDF fixture", lambda: test_pdf.write_bytes(content))
            pages = run_stage("PyPDF extraction", lambda: extract_pdf_pages(test_pdf))
            chunks = run_stage("page-aware text chunking", lambda: chunk_pages(pages))

            embeddings = run_stage(f"load real embedding model {model_name}", get_embeddings)
            vectors = run_stage(
                "generate real sentence-transformer embedding",
                lambda: embeddings.embed_documents([chunk.text for chunk in chunks]),
            )
            if not vectors or not vectors[0]:
                raise RuntimeError("The configured embedding model returned an empty vector.")
            logger.info("Embedding dimension: %d", len(vectors[0]))

            isolated_store = LocalVectorStore(temp_root / "faiss-index")
            run_stage(
                "create and persist isolated FAISS index",
                lambda: isolated_store.add_chunks(chunks, "standalone-smoke", test_pdf.name),
            )
            retrieved = run_stage(
                "reload/search isolated FAISS index",
                lambda: LocalVectorStore(temp_root / "faiss-index").search("database normalization", 1),
            )
            if not retrieved:
                raise RuntimeError("FAISS index returned no results for the smoke-test query.")

        # Exercise the actual production API path. The endpoint stores and indexes
        # this PDF using the configured data directories, then cleanup removes it.
        with TestClient(app) as client:
            metadata_file = settings.memory_dir / "documents.json"
            metadata_existed_before_test = metadata_file.exists()
            test_document_id = None
            try:
                upload_response = run_stage(
                    "FastAPI PDF upload and production FAISS indexing",
                    lambda: client.post(
                        "/api/documents/upload",
                        files={"file": ("dbms-embedding-smoke-test.pdf", content, "application/pdf")},
                    ),
                )
                if upload_response.status_code != 201:
                    raise RuntimeError(
                        f"Upload API returned HTTP {upload_response.status_code}: "
                        f"{upload_response.text}"
                    )
                document = upload_response.json()
                test_document_id = document["id"]
                if document.get("status") != "ready" or document.get("chunks", 0) < 1:
                    raise RuntimeError(f"Upload response did not confirm an indexed PDF: {document}")
                logger.info(
                    "Upload indexed %d page(s) into %d chunk(s), id=%s",
                    document["pages"],
                    document["chunks"],
                    document["id"],
                )
                result = vector_store.search("database normalization", 1)
                if not result:
                    raise RuntimeError("Production FAISS index could not retrieve the uploaded test PDF.")
            finally:
                if test_document_id:
                    deleted = client.delete(f"/api/documents/{test_document_id}")
                    if deleted.status_code != 200:
                        logger.error(
                            "Test document cleanup failed: HTTP %s %s",
                            deleted.status_code,
                            deleted.text,
                        )
                    else:
                        logger.info(
                            "Removed temporary uploaded smoke-test PDF and rebuilt the production index."
                        )
                if (
                    not metadata_existed_before_test
                    and metadata_file.exists()
                    and metadata_file.read_text(encoding="utf-8").strip() == "[]"
                ):
                    metadata_file.unlink()

    except Exception:
        logger.error("Embedding/PDF pipeline verification failed.")
        traceback.print_exc()
        return 1

    logger.info("SUCCESS: model load, real embeddings, PDF pipeline, FAISS, and upload API verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
