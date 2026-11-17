import { useCallback, useEffect, useState } from "react";
import { LoaderCircle, WifiOff } from "lucide-react";
import ActivityPage from "./pages/ActivityPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import ChatPage from "./pages/ChatPage";
import Dashboard from "./pages/Dashboard";
import DocumentsPage from "./pages/DocumentsPage";
import PlannerPage from "./pages/PlannerPage";
import QuizPage from "./pages/QuizPage";
import PageHeader from "./components/PageHeader";
import Sidebar from "./components/Sidebar";
import Notice from "./components/Notice";
import { api } from "./services/api";
import type { ActivityEvent, DocumentItem, Quiz, QuizResult, Section, StudyPlan } from "./types";

type Performance = {
  quiz_count: number;
  average_score: number;
  topic_scores: Record<string, number>;
  strong_topics: string[];
  weak_topics: string[];
  recommendations: string[];
  history: QuizResult[];
  learning_history: { type: string; subject: string; summary: string; created_at: string }[];
};
const EMPTY_PERFORMANCE: Performance = { quiz_count: 0, average_score: 0, topic_scores: {}, strong_topics: [], weak_topics: [], recommendations: [], history: [], learning_history: [] };

export default function App() {
  const [section, setSection] = useState<Section>("dashboard");
  const [collapsed, setCollapsed] = useState(() => window.innerWidth < 900);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [performance, setPerformance] = useState<Performance>(EMPTY_PERFORMANCE);
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [pendingQuiz, setPendingQuiz] = useState<Quiz | null>(null);
  const [llmConfigured, setLlmConfigured] = useState(false);
  const [backendOnline, setBackendOnline] = useState(true);
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [health, docs, plans, progress, activity] = await Promise.all([
        api.health(), api.documents(), api.studyPlan(), api.performance(), api.activity(),
      ]);
      setBackendOnline(true); setLlmConfigured(health.llm_configured);
      setDocuments(docs); setPlan(plans.current); setPerformance({ ...EMPTY_PERFORMANCE, ...progress }); setEvents(activity);
    } catch (error) {
      setBackendOnline(false);
      if (error instanceof Error && !error.message.includes("fetch")) setNotice(error.message);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void refresh(); const timer = window.setInterval(() => { void refresh(); }, 5000); return () => window.clearInterval(timer); }, [refresh]);

  function showQuiz(quiz: Quiz) { setPendingQuiz(quiz); setSection("quiz"); }
  const notify = (message: string) => { setNotice(message); window.setTimeout(() => setNotice(""), 7000); };

  let page;
  if (loading) page = <div className="grid min-h-[50vh] place-items-center"><div className="flex items-center gap-2 text-sm text-muted"><LoaderCircle className="animate-spin" size={17} /> Connecting to your local study space…</div></div>;
  else if (!backendOnline) page = <div className="grid min-h-[50vh] place-items-center rounded-2xl border border-dashed border-line bg-white p-8 text-center"><div><WifiOff size={25} className="mx-auto text-muted" /><h2 className="mt-3 font-display text-lg font-bold">Your local backend isn’t responding</h2><p className="mt-1 text-xs text-muted">Start the FastAPI server at 127.0.0.1:8000, then refresh this page.</p></div></div>;
  else switch (section) {
    case "dashboard": page = <Dashboard documents={documents} plan={plan} performance={performance} activity={events} onNavigate={setSection} />; break;
    case "chat": page = <ChatPage hasDocuments={documents.length > 0} onQuiz={showQuiz} onPlan={setPlan} />; break;
    case "documents": page = <DocumentsPage documents={documents} onRefresh={refresh} notify={notify} />; break;
    case "planner": page = <PlannerPage plan={plan} onPlan={setPlan} onQuiz={setPendingQuiz} onNavigateQuiz={() => setSection("quiz")} notify={notify} />; break;
    case "quiz": page = <QuizPage initialQuiz={pendingQuiz} onQuizConsumed={() => setPendingQuiz(null)} onRefresh={refresh} notify={notify} />; break;
    case "analytics": page = <AnalyticsPage performance={performance} />; break;
    case "activity": page = <ActivityPage events={events} />; break;
  }

  return <div className="min-h-screen bg-canvas">
    <Sidebar active={section} onChange={setSection} collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} />
    <main className={`min-h-screen transition-[margin] duration-200 ${collapsed ? "ml-[76px]" : "ml-[248px]"}`}>
      <div className="mx-auto max-w-[1440px] px-5 py-7 sm:px-7 lg:px-10 lg:py-9">
        <PageHeader section={section} llmConfigured={llmConfigured} />
        {!llmConfigured && backendOnline && <div className="mb-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-900"><strong>Finish your local AI setup.</strong> In the project-root <code className="rounded bg-white/70 px-1">.env</code>, fill <code>OPENAI_API_KEY</code>, <code>OPENAI_BASE_URL</code>, and <code>OPENAI_MODEL</code>. These values stay on the backend; they are never sent to the browser.</div>}
        <Notice message={notice} onDismiss={() => setNotice("")} />
        {page}
      </div>
    </main>
  </div>;
}
