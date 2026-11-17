export type Section = "dashboard" | "chat" | "documents" | "planner" | "quiz" | "analytics" | "activity";

export interface DocumentItem {
  id: string;
  name: string;
  pages: number;
  chunks: number;
  size_bytes: number;
  status: string;
}

export interface Citation {
  document_id: string;
  document_name: string;
  page: number;
  label?: string;
}

export interface StudySession {
  day: number;
  date: string;
  focus: string;
  tasks: string[];
  duration_hours: number;
}

export interface StudyPlan {
  id: string;
  title: string;
  rationale: string;
  subject: string;
  exam_date: string;
  hours_per_day: number;
  sessions: StudySession[];
}

export interface QuizQuestion {
  prompt: string;
  options: string[];
  topic: string;
  question_type: "mcq" | "short_answer";
}

export interface Quiz {
  id: string;
  title: string;
  subject: string;
  topic: string;
  difficulty: string;
  questions: QuizQuestion[];
  citations?: Citation[];
}

export interface ActivityEvent {
  id: string;
  agent: string;
  status: string;
  message: string;
  details?: string | null;
  created_at: string;
}

export interface QuizResult {
  id: string;
  quiz_id: string;
  subject: string;
  score: number;
  total: number;
  score_percent: number;
  created_at?: string;
  topic_scores: Record<string, number>;
  feedback: { question_index: number; correct: boolean; your_answer: string; correct_answer: string; explanation: string; topic: string }[];
  adaptive_explanation?: string | null;
  retry_quiz?: Quiz | null;
  adaptive_error?: string;
}
