import json
import logging
import threading
from pathlib import Path
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)
_lock = threading.RLock()

DEFAULTS: dict[str, Any] = {
    "student_profile.json": {},
    "learning_history.json": [],
    "quiz_results.json": [],
    "study_plans.json": [],
    "preferences.json": {"explanation_mode": "simple"},
    "agent_activity.json": [],
    "quizzes.json": {},
    "documents.json": [],
}


class JsonStorage:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or get_settings().memory_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        if name not in DEFAULTS:
            raise ValueError(f"Unsupported memory file: {name}")
        return self.base_dir / name

    def read(self, name: str) -> Any:
        path = self._path(name)
        with _lock:
            if not path.exists():
                return DEFAULTS[name].copy()
            try:
                with path.open("r", encoding="utf-8") as file:
                    value = json.load(file)
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Could not read %s: %s", path, exc)
                return DEFAULTS[name].copy()
            return value

    def write(self, name: str, value: Any) -> None:
        path = self._path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        with _lock:
            try:
                with temp.open("w", encoding="utf-8") as file:
                    json.dump(value, file, ensure_ascii=False, indent=2)
                    file.flush()
                temp.replace(path)
            except OSError:
                temp.unlink(missing_ok=True)
                raise

    def append(self, name: str, item: Any) -> list[Any]:
        with _lock:
            current = self.read(name)
            if not isinstance(current, list):
                raise ValueError(f"{name} must contain a JSON list")
            current.append(item)
            self.write(name, current)
            return current


storage = JsonStorage()
