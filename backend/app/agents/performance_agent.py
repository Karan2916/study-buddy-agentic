from typing import Any

from app.memory.memory_manager import performance_snapshot, record_activity


def analyze(result: dict[str, Any]) -> dict[str, Any]:
    snapshot = performance_snapshot()
    weak = [topic for topic, score in result.get("topic_scores", {}).items() if score < 60]
    strong = [topic for topic, score in result.get("topic_scores", {}).items() if score >= 75]
    recommendations = [
        f"Review {topic} with the Tutor Agent, then retry with a fresh practice quiz."
        for topic in weak
    ]
    record_activity(
        "Performance Agent",
        "completed",
        f"Analyzed score {result.get('score_percent', 0)}%; "
        f"{len(weak)} weak and {len(strong)} strong topics identified.",
        f"Weak: {', '.join(weak) or 'none'}; strong: {', '.join(strong) or 'none'}",
    )
    return {
        **snapshot,
        "current_weak_topics": weak,
        "current_strong_topics": strong,
        "recommendations": recommendations or snapshot["recommendations"],
    }
