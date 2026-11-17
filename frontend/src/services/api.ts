import type { ActivityEvent, Citation, DocumentItem, Quiz, QuizResult, StudyPlan } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail ?? `Request failed (${response.status})`);
  }
  return payload as T;
}

export const api = {
  health: () => request<{ status: string; llm_configured: boolean; missing_llm_settings: string[] }>("/api/health"),
  documents: () => request<DocumentItem[]>("/api/documents"),
  upload: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<DocumentItem>("/api/documents/upload", { method: "POST", body });
  },
  deleteDocument: (id: string) => request(`/api/documents/${id}`, { method: "DELETE" }),
  chat: (message: string, mode: string, subject?: string) =>
    request<{ answer: string; agents: string[]; citations: Citation[]; quiz?: Quiz; plan?: StudyPlan }>("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, mode, subject }),
    }),
  examPrep: (body: { subject: string; exam_date: string; hours_per_day: number }) =>
    request<{ plan: StudyPlan; research: { topics: string[]; citations: Citation[] }; explanation: string; quiz: Quiz }>("/api/workflows/exam-preparation", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    }),
  makePlan: (body: { subject: string; exam_date: string; hours_per_day: number }) =>
    request<{ plan: StudyPlan; topics: string[]; citations: Citation[] }>("/api/study-plan/generate", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    }),
  studyPlan: () => request<{ current: StudyPlan | null; history: StudyPlan[] }>("/api/study-plan"),
  generateQuiz: (body: { subject: string; topic: string; difficulty: string; question_count: number }) =>
    request<Quiz>("/api/quiz/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }),
  adaptiveLearning: (body: { subject: string; topic: string; mode: string; difficulty: string; question_count: number }) =>
    request<{ explanation: string; quiz: Quiz; citations: Citation[] }>("/api/workflows/adaptive-learning", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    }),
  submitQuiz: (quiz_id: string, answers: Record<string, string>) =>
    request<QuizResult>("/api/quiz/submit", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ quiz_id, answers }) }),
  quizHistory: () => request<QuizResult[]>("/api/quiz/history"),
  performance: () => request<{ quiz_count: number; average_score: number; topic_scores: Record<string, number>; strong_topics: string[]; weak_topics: string[]; recommendations: string[]; history: QuizResult[]; learning_history: { type: string; subject: string; summary: string; created_at: string }[] }>("/api/performance"),
  activity: () => request<ActivityEvent[]>("/api/agents/activity"),
  revisionKit: (subject: string, topic: string) => request<{ kit: Record<string, string[]>; citations: Citation[] }>("/api/workflows/revision-kit", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ subject, topic }),
  }),
  knowledgeGaps: (subject: string) => request<{ topics_in_material: string[]; topic_scores: Record<string, number>; weak_topics: string[]; unstudied_topics: string[]; recommendations: { topic: string; priority: string; reason: string }[]; citations: Citation[] }>("/api/workflows/knowledge-gaps", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ subject }),
  }),
};
