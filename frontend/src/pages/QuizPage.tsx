import { FormEvent, useState } from "react";
import { BrainCircuit, Check, CircleHelp, LoaderCircle, RotateCcw, Send, Sparkles, X } from "lucide-react";
import CitationList from "../components/CitationList";
import EmptyState from "../components/EmptyState";
import Notice from "../components/Notice";
import type { Quiz, QuizResult } from "../types";
import { api } from "../services/api";

export default function QuizPage({ initialQuiz, onQuizConsumed, onRefresh, notify }: { initialQuiz: Quiz | null; onQuizConsumed: () => void; onRefresh: () => Promise<void>; notify: (message: string) => void }) {
  const [subject, setSubject] = useState("DBMS");
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState("medium");
  const [count, setCount] = useState(5);
  const [quiz, setQuiz] = useState<Quiz | null>(initialQuiz);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function loadQuiz(next: Quiz) {
    setQuiz(next); setAnswers({}); setResult(null); setError(""); onQuizConsumed();
  }
  function resetQuiz() {
    setQuiz(null); setAnswers({}); setResult(null); onQuizConsumed();
  }
  async function generate(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError("");
    try { loadQuiz(await api.generateQuiz({ subject, topic, difficulty, question_count: count })); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Quiz generation failed."); }
    finally { setLoading(false); }
  }
  async function submit(event: FormEvent) {
    event.preventDefault(); if (!quiz) return;
    setLoading(true); setError("");
    try {
      const graded = await api.submitQuiz(quiz.id, answers);
      setResult(graded);
      if (graded.retry_quiz) {
        setQuiz(graded.retry_quiz);
        setAnswers({});
      }
      await onRefresh();
      notify("Your quiz result was saved to local learning history.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not submit the quiz."); }
    finally { setLoading(false); }
  }

  return <div className="animate-fade-in">
    {error && <Notice message={error} onDismiss={() => setError("")} />}
    {!quiz && <div className="grid gap-5 xl:grid-cols-[.7fr_1.3fr]">
      <form onSubmit={(event) => void generate(event)} className="h-fit rounded-2xl border border-line bg-white p-5 shadow-card sm:p-6">
        <div className="mb-5 flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-xl bg-[#f3f7de] text-[#728532]"><BrainCircuit size={19} /></div><div><h2 className="font-display text-lg font-bold">Practice on purpose</h2><p className="text-[11px] text-muted">Questions come from your indexed materials.</p></div></div>
        <label className="mb-1.5 block text-xs font-bold">Subject</label><input required value={subject} onChange={(e) => setSubject(e.target.value)} className="mb-4 w-full rounded-xl border border-line bg-[#fbfcfa] px-3 py-2.5 text-sm outline-none focus:border-[#9bb399]" />
        <label className="mb-1.5 block text-xs font-bold">Topic <span className="font-normal text-muted">(optional)</span></label><input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="e.g. Normalization" className="mb-4 w-full rounded-xl border border-line bg-[#fbfcfa] px-3 py-2.5 text-sm outline-none focus:border-[#9bb399]" />
        <div className="mb-4 grid grid-cols-2 gap-3"><div><label className="mb-1.5 block text-xs font-bold">Difficulty</label><select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} className="w-full rounded-xl border border-line bg-[#fbfcfa] px-3 py-2.5 text-sm outline-none"><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></div><div><label className="mb-1.5 block text-xs font-bold">Questions</label><select value={count} onChange={(e) => setCount(Number(e.target.value))} className="w-full rounded-xl border border-line bg-[#fbfcfa] px-3 py-2.5 text-sm outline-none">{[3, 5, 10, 15, 20].map((n) => <option key={n}>{n}</option>)}</select></div></div>
        <button disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-xl bg-forest py-3 text-xs font-bold text-white disabled:opacity-50">{loading ? <LoaderCircle size={15} className="animate-spin" /> : <Sparkles size={15} />}{loading ? "Creating your quiz…" : "Generate quiz"}</button>
      </form>
      <EmptyState icon={<CircleHelp size={21} />} title="A little practice goes a long way" description="Create a short quiz from your course materials. Your answers help your performance agent spot what to work on next." />
    </div>}

    {quiz && <div className="mx-auto max-w-3xl">
      {result && <section className={`mb-5 rounded-2xl border p-5 ${result.score_percent < 60 ? "border-[#f0dfd3] bg-[#fff9f5]" : "border-[#dfe8dc] bg-[#f2f7ef]"}`}>
        <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-[10px] font-bold uppercase tracking-[.15em] text-muted">YOUR RESULT</p><h2 className="mt-1 font-display text-2xl font-bold">{result.score}/{result.total} correct <span className="text-forest">· {result.score_percent}%</span></h2><p className="mt-1 text-xs text-muted">Performance Agent saved your progress and updated your topic history.</p></div><div className="grid h-14 w-14 place-items-center rounded-full border-4 border-forest font-display text-sm font-bold text-forest">{result.score_percent}%</div></div>
        {result.feedback.length > 0 && <div className="mt-4 space-y-2">{result.feedback.map((item) => <div key={item.question_index} className="rounded-xl bg-white/80 p-3"><div className="flex items-start gap-2">{item.correct ? <Check size={14} className="mt-0.5 text-emerald-600" /> : <X size={14} className="mt-0.5 text-rose-500" />}<div className="text-xs"><p className="font-bold">{item.topic} · {item.correct ? "Correct" : "Review this one"}</p><p className="mt-1 text-muted">Answer: <span className="font-semibold text-ink">{item.correct_answer || "See course material"}</span></p><p className="mt-1 leading-5 text-muted">{item.explanation}</p></div></div></div>)}</div>}
        {result.adaptive_explanation && <div className="mt-4 rounded-xl border border-[#e5ebe2] bg-white p-4"><p className="mb-2 flex items-center gap-2 text-xs font-bold text-forest"><Sparkles size={14} /> Tutor’s adaptive explanation</p><p className="whitespace-pre-wrap text-xs leading-6 text-[#59665f]">{result.adaptive_explanation}</p></div>}
        {result.adaptive_error && <p className="mt-3 text-xs text-rose-700">{result.adaptive_error}</p>}
        {result.retry_quiz && <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-xl bg-white p-3"><p className="text-xs font-semibold">A fresh targeted retry is ready. Submit it to continue strengthening this topic.</p><span className="text-[10px] font-bold text-forest">NEW QUIZ LOADED ↓</span></div>}
        {result && !result.retry_quiz && result.score_percent >= 60 && <button onClick={resetQuiz} className="mt-4 inline-flex items-center gap-2 rounded-lg bg-forest px-3 py-2 text-xs font-bold text-white"><RotateCcw size={13} /> Try another quiz</button>}
      </section>}
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3"><div><p className="text-[10px] font-bold uppercase tracking-[.15em] text-forest">{quiz.subject} · {quiz.difficulty}</p><h2 className="mt-1 font-display text-xl font-bold">{quiz.title}</h2><p className="mt-1 text-xs text-muted">{quiz.questions.length} questions · Answers stay hidden until submission</p></div>{!result && <button onClick={resetQuiz} className="rounded-lg border border-line bg-white px-3 py-2 text-[11px] font-semibold text-muted hover:text-ink">New quiz</button>}</div>
      {quiz.citations && <CitationList citations={quiz.citations} />}
      <form onSubmit={(event) => void submit(event)} className="mt-4 space-y-3">
        {quiz.questions.map((question, index) => <article key={`${quiz.id}-${index}`} className="rounded-2xl border border-line bg-white p-4 shadow-card sm:p-5"><div className="mb-3 flex items-start gap-3"><span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-[#eef4ea] text-[10px] font-extrabold text-forest">{String(index + 1).padStart(2, "0")}</span><div><p className="text-sm font-semibold leading-6">{question.prompt}</p><span className="mt-1 inline-block rounded-md bg-canvas px-2 py-1 text-[9px] font-bold text-muted">{question.topic}</span></div></div>
            {question.options.length ? <div className="ml-10 grid gap-2 sm:grid-cols-2">{question.options.map((option, optionIndex) => <label key={optionIndex} className={`flex cursor-pointer items-start gap-2 rounded-xl border px-3 py-2.5 text-xs leading-5 transition-colors ${answers[String(index)] === option ? "border-[#9cb899] bg-[#f2f7ef]" : "border-line hover:border-[#cbd8c8]"}`}><input type="radio" name={`question-${index}`} checked={answers[String(index)] === option} onChange={() => setAnswers((current) => ({ ...current, [String(index)]: option }))} disabled={Boolean(result && !result.retry_quiz)} className="mt-0.5 accent-[#1d5948]" />{option}</label>)}</div>
            : <textarea disabled={Boolean(result && !result.retry_quiz)} value={answers[String(index)] ?? ""} onChange={(e) => setAnswers((current) => ({ ...current, [String(index)]: e.target.value }))} rows={2} placeholder="Write your answer…" className="ml-10 w-[calc(100%-2.5rem)] rounded-xl border border-line px-3 py-2 text-xs outline-none focus:border-[#9cb899]" />}
          </article>)}
        {(!result || result.retry_quiz) && <button disabled={loading || Boolean(result && !result.retry_quiz)} className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl bg-forest py-3 text-xs font-bold text-white disabled:opacity-50">{loading ? <LoaderCircle size={15} className="animate-spin" /> : <Send size={14} />}{loading ? "Scoring and analyzing…" : result?.retry_quiz ? "Submit retry quiz" : "Submit my answers"}</button>}
      </form>
    </div>}
  </div>;
}
