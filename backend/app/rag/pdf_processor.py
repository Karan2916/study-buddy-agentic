from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


@dataclass(frozen=True)
class TextChunk:
    text: str
    page_number: int


def extract_pdf_pages(path: Path) -> list[PageText]:
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as exc:
                raise ValueError(f"PDF is encrypted and cannot be opened: {path.name}") from exc
        pages = [
            PageText(index + 1, (page.extract_text() or "").strip())
            for index, page in enumerate(reader.pages)
        ]
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError(f"Could not read PDF '{path.name}': {exc}") from exc
    if not any(page.text for page in pages):
        raise ValueError(
            f"No extractable text found in '{path.name}'. Scanned PDFs require OCR, "
            "which is not enabled."
        )
    return pages


def chunk_pages(
    pages: list[PageText], chunk_size: int = 1000, overlap: int = 150
) -> list[TextChunk]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and overlap must be smaller than chunk_size")
    chunks: list[TextChunk] = []
    stride = chunk_size - overlap
    for page in pages:
        text = " ".join(page.text.split())
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            piece = text[start:end].strip()
            if piece:
                chunks.append(TextChunk(piece, page.page_number))
            if end == len(text):
                break
            start += stride
    return chunks
