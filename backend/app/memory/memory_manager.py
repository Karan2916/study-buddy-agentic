from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.storage.json_storage import storage


def record_activity(agent: str, status: str, message: str, details: str | None = None) -> dict[str, Any]:
    event = {
        "id": str(uuid4()),
        "agent": agent,
        "status": status,
        "message": message,
        "details": details,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    storage.append("agent_activity.json", event)
    return event


def record_learning_event(event_type: str, subject: str, summary: str) -> None:
    storage.append(
        "learning_history.json",
        {
            "id": str(uuid4()),
            "type": event_type,
            "subject": subject,
            "summary": summary,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def performance_snapshot() -> dict[str, Any]:
    results = storage.read("quiz_results.json")
    topics: dict[str, list[float]] = {}
    for result in results if isinstance(results, list) else []:
        for topic, score in (result.get("topic_scores") or {}).items():
            topics.setdefault(topic, []).append(float(score))
    averages = {topic: sum(scores) / len(scores) for topic, scores in topics.items()}
    return {
        "quiz_count": len(results) if isinstance(results, list) else 0,
        "average_score": (
            sum(float(r.get("score_percent", 0)) for r in results) / len(results)
            if isinstance(results, list) and results
            else 0
        ),
        "topic_scores": averages,
        "strong_topics": [topic for topic, score in averages.items() if score >= 75],
        "weak_topics": [topic for topic, score in averages.items() if score < 60],
        "recommendations": [
            f"Review {topic} and complete targeted practice."
            for topic, score in averages.items()
            if score < 60
        ],
    }
