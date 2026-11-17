import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import chat, documents, performance, quizzes, study_plans, workflows
from app.api.models import HealthResponse
from app.core.config import get_settings
from app.memory.memory_manager import record_activity

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()
settings.documents_dir.mkdir(parents=True, exist_ok=True)
settings.index_dir.mkdir(parents=True, exist_ok=True)
settings.memory_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Study Buddy AI",
    description="Local multi-agent personalized learning assistant",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.frontend_port}",
        f"http://127.0.0.1:{settings.frontend_port}",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(workflows.router)
app.include_router(quizzes.router)
app.include_router(study_plans.router)
app.include_router(performance.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled request error", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred."})


@app.get("/api/health", response_model=HealthResponse)
def health():
    missing = settings.missing_llm_settings()
    return {
        "status": "ok",
        "llm_configured": not missing,
        "missing_llm_settings": missing,
        "embedding_model": settings.embedding_model,
        "storage": "local-json-and-faiss",
    }
