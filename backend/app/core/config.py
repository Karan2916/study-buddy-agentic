from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="", alias="OPENAI_MODEL")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL",
    )
    backend_host: str = Field(default="127.0.0.1", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    frontend_port: int = Field(default=5173, alias="FRONTEND_PORT")

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    def missing_llm_settings(self) -> list[str]:
        required = {
            "OPENAI_API_KEY": self.openai_api_key,
            "OPENAI_BASE_URL": self.openai_base_url,
            "OPENAI_MODEL": self.openai_model,
        }
        return [
            key
            for key, value in required.items()
            if not value.strip() or value.strip().startswith("PASTE_YOUR_")
        ]

    def validate_llm_settings(self) -> None:
        missing = self.missing_llm_settings()
        if missing:
            names = ", ".join(missing)
            raise RuntimeError(
                f"GPT-4.1-mini is not configured. Fill in {names} in the "
                f"project-root .env file (copy .env.example as a guide)."
            )

    @property
    def data_dir(self) -> Path:
        return PROJECT_ROOT / "data"

    @property
    def documents_dir(self) -> Path:
        return self.data_dir / "documents"

    @property
    def index_dir(self) -> Path:
        return self.data_dir / "faiss_index"

    @property
    def memory_dir(self) -> Path:
        return self.data_dir / "memory"


@lru_cache
def get_settings() -> Settings:
    return Settings()
