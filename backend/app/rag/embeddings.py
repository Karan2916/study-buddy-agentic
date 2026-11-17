import logging
from functools import lru_cache
from pathlib import Path

from huggingface_hub.constants import HF_HUB_CACHE
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_embeddings() -> HuggingFaceEmbeddings:
    model_name = get_settings().embedding_model
    cache_dir = Path(HF_HUB_CACHE).expanduser().resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        "Loading embedding model %r on CPU; Hugging Face cache: %s",
        model_name,
        cache_dir,
    )
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            cache_folder=str(cache_dir),
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    except Exception:
        logger.exception(
            "Embedding model load failed; model=%r cache_dir=%s",
            model_name,
            cache_dir,
        )
        raise
    logger.info("Embedding model %r loaded successfully.", model_name)
    return embeddings
