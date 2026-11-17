from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    mode: Literal["simple", "detailed", "examples", "exam"] = "simple"
    subject: str | None = None


class ChatResponse(BaseModel):
    answer: str
    agents: list[str]
    citations: list[CitationResponse]
    quiz: QuizResponse | None = None
    plan: StudyPlanResponse | None = None


class ExamPreparationRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=120)
    exam_date: date
    hours_per_day: float = Field(gt=0, le=24)


class AdaptiveLearningRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=120)
    topic: str = Field(min_length=1, max_length=240)
    mode: Literal["simple", "detailed", "examples", "exam"] = "simple"
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    question_count: int = Field(default=5, ge=1, le=20)


class RevisionKitRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=120)
    topic: str = Field(default="", max_length=240)


class KnowledgeGapsRequest(BaseModel):
    subject: str = Field(default="", max_length=120)


class QuizGenerateRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=120)
    topic: str = Field(default="", max_length=240)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    question_count: int = Field(default=5, ge=1, le=20)


class QuizSubmitRequest(BaseModel):
    quiz_id: str
    answers: dict[str, str]


class StudyPlanRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=120)
    exam_date: date
    hours_per_day: float = Field(gt=0, le=24)


class ErrorResponse(BaseModel):
    detail: str


class CitationResponse(BaseModel):
    document_id: str
    document_name: str
    page: int
    label: str | None = None


class DocumentResponse(BaseModel):
    id: str
    name: str
    pages: int
    chunks: int
    size_bytes: int
    status: str


class QuizQuestionResponse(BaseModel):
    prompt: str
    options: list[str]
    topic: str
    question_type: Literal["mcq", "short_answer"]


class QuizResponse(BaseModel):
    id: str
    title: str
    subject: str
    topic: str = ""
    difficulty: str
    questions: list[QuizQuestionResponse]
    citations: list[CitationResponse] = Field(default_factory=list)


class StudySessionResponse(BaseModel):
    day: int
    date: str
    focus: str
    tasks: list[str]
    duration_hours: float


class StudyPlanResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    title: str
    rationale: str
    subject: str
    exam_date: str
    hours_per_day: float
    topics: list[str] = Field(default_factory=list)
    sessions: list[StudySessionResponse]


class StudyPlanEnvelope(BaseModel):
    current: StudyPlanResponse | None
    history: list[StudyPlanResponse]


class GeneratedStudyPlanResponse(BaseModel):
    plan: StudyPlanResponse
    topics: list[str]
    citations: list[CitationResponse]


class ResearchResponse(BaseModel):
    topics: list[str] = Field(default_factory=list)
    summary: str
    missing_information: list[str] = Field(default_factory=list)
    chunks: list[dict] = Field(default_factory=list)
    citations: list[CitationResponse] = Field(default_factory=list)


class ExamPreparationResponse(BaseModel):
    research: ResearchResponse
    plan: StudyPlanResponse
    explanation: str
    quiz: QuizResponse


class AdaptiveLearningResponse(BaseModel):
    explanation: str
    quiz: QuizResponse
    citations: list[CitationResponse]


class RevisionKitResponse(BaseModel):
    kit: dict[str, list[str]]
    citations: list[CitationResponse]


class QuizFeedbackResponse(BaseModel):
    question_index: int
    correct: bool
    your_answer: str
    correct_answer: str
    explanation: str
    topic: str


class QuizResultResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    quiz_id: str
    subject: str
    score: int
    total: int
    score_percent: int
    topic_scores: dict[str, int]
    feedback: list[QuizFeedbackResponse]
    performance: dict = Field(default_factory=dict)
    adaptive_explanation: str | None = None
    retry_quiz: QuizResponse | None = None
    updated_plan: StudyPlanResponse | None = None
    adaptive_error: str | None = None
    plan_adaptation_error: str | None = None


class KnowledgeGapResponse(BaseModel):
    topics_in_material: list[str]
    topic_scores: dict[str, float]
    weak_topics: list[str]
    unstudied_topics: list[str]
    recommendations: list[dict[str, str]]
    citations: list[CitationResponse]


class ActivityEventResponse(BaseModel):
    id: str
    agent: str
    status: str
    message: str
    details: str | None = None
    created_at: str


class PerformanceResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    quiz_count: int
    average_score: float
    topic_scores: dict[str, float]
    strong_topics: list[str]
    weak_topics: list[str]
    recommendations: list[str]


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool
    missing_llm_settings: list[str]
    embedding_model: str
    storage: str
