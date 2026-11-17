import { FormEvent, useState } from "react";
import { ArrowRight, CalendarDays, Check, Clock3, LoaderCircle, Sparkles } from "lucide-react";
import CitationList from "../components/CitationList";
import EmptyState from "../components/EmptyState";
import type { Citation, Quiz, StudyPlan } from "../types";
import { api } from "../services/api";

function defaultExamDate() {
  const date = new Date();
  date.setDate(date.getDate() + 3);
  return date.toISOString().slice(0, 10);
}

export default function PlannerPage({ plan, onPlan, onQuiz, onNavigateQuiz, notify }: { plan: StudyPlan | null; onPlan: (plan: StudyPlan) => void; onQuiz: (quiz: Quiz) => void; onNavigateQuiz: () => void; notify: (message: string) => void }) {
  const [subject, setSubject] = useState(plan?.subject ?? "DBMS");
  const [examDate, setExamDate] = useState(plan?.exam_date ?? defaultExamDate());
  const [hours, setHours] = useState(plan?.hours_per_day ?? 3);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [explanation, setExplanation] = useState("");
  const [busy, setBusy] = useState(false);

  async function create(event: FormEvent) {
    event.preventDefault(); setBusy(true); setExplanation(""); setCitations([]);
    try {
      const result = await api.examPrep({ subject, exam_date: examDate, hours_per_day: Number(hours) });
      onPlan(result.plan); onQuiz(result.quiz); setCitations(result.research.citations); setExplanation(result.explanation);
      notify("Your research-backed plan and diagnostic quiz are ready.");
    } catch (error) { notify(error instanceof Error ? error.message : "Could not create the study plan."); }
    finally { setBusy(false); }
  }
  return <div className="animate-fade-in">
    <div className="grid gap-5 xl:grid-cols-[.72fr_1.28fr]">
      <form onSubmit={(event) => void create(event)} className="h-fit rounded-2xl border border-line bg-white p-5 shadow-card sm:p-6">
        <div className="mb-5 flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-xl bg-[#eef4ea] text-forest"><CalendarDays size={19} /></div><div><h2 className="font-display text-lg font-bold">Tell us your goal</h2><p className="text-[11px] text-muted">Your agents will take it from there.</p></div></div>
        <label className="mb-1.5 block text-xs font-bold">What are you studying?</label><input required value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="e.g. Database Management Systems" className="mb-4 w-full rounded-xl border border-line bg-[#fbfcfa] px-3 py-2.5 text-sm outline-none focus:border-[#9bb399]" />
        <label className="mb-1.5 block text-xs font-bold">When is your exam?</label><input required type="date" min={new Date().toISOString().slice(0, 10)} value={examDate} onChange={(e) => setExamDate(e.target.value)} className="mb-4 w-full rounded-xl border border-line bg-[#fbfcfa] px-3 py-2.5 text-sm outline-none focus:border-[#9bb399]" />
        <label className="mb-1.5 block text-xs font-bold">How much time can you study per day?</label><div className="relative mb-5"><Clock3 size={15} className="absolute left-3 top-3 text-muted" /><input required type="number" step="0.5" min="0.5" max="24" value={hours} onChange={(e) => setHours(Number(e.target.value))} className="w-full rounded-xl border border-line bg-[#fbfcfa] py-2.5 pl-9 pr-14 text-sm outline-none focus:border-[#9bb399]" /><span className="absolute right-3 top-3 text-xs text-muted">hours/day</span></div>
        <button disabled={busy} className="flex w-full items-center justify-center gap-2 rounded-xl bg-forest py-3 text-xs font-bold text-white hover:bg-[#174b3d] disabled:opacity-60">{busy ? <><LoaderCircle size={15} className="animate-spin" /> Agents are building your plan…</> : <><Sparkles size={15} /> Build my personalized plan</>}</button>
        {busy && <p className="mt-3 text-center text-[10px] leading-5 text-muted">Research → Planner → Tutor → Quiz. This can take a minute while the local embedding model loads.</p>}
      </form>

      <section>
        {plan ? <div className="rounded-2xl border border-line bg-white p-5 shadow-card sm:p-6">
          <div className="mb-5 flex flex-wrap items-start justify-between gap-3"><div><p className="text-[10px] font-bold uppercase tracking-[.15em] text-forest">STUDY PLAN · {plan.subject}</p><h2 className="mt-1 font-display text-xl font-bold">{plan.title}</h2><p className="mt-1 text-xs text-muted">{plan.rationale}</p></div><div className="rounded-xl bg-[#eef4ea] px-3 py-2 text-right"><p className="text-xs font-bold text-forest">{plan.exam_date}</p><p className="text-[10px] text-muted">{plan.hours_per_day} hours/day</p></div></div>
          <div className="space-y-3">{plan.sessions.map((session) => <article key={`${session.day}-${session.date}`} className="relative flex gap-3 rounded-xl border border-line p-4">
            <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-[#eef4ea] text-xs font-extrabold text-forest">{String(session.day).padStart(2, "0")}</div>
            <div className="min-w-0 flex-1"><div className="flex flex-wrap items-center justify-between gap-2"><h3 className="text-sm font-bold">{session.focus}</h3><span className="text-[10px] font-semibold text-muted">{session.date} · {session.duration_hours}h</span></div><ul className="mt-2 space-y-1.5">{session.tasks.map((task, index) => <li key={index} className="flex gap-2 text-xs leading-5 text-[#59665f]"><Check size={13} className="mt-1 shrink-0 text-forest" />{task}</li>)}</ul></div>
          </article>)}</div>
          {explanation && <div className="mt-5 rounded-xl bg-[#f3f7ef] p-4"><div className="mb-2 flex items-center gap-2 text-xs font-bold text-forest"><Sparkles size={14} /> Tutor’s focus notes</div><p className="whitespace-pre-wrap text-xs leading-6 text-[#59665f]">{explanation}</p></div>}
          <CitationList citations={citations} />
          <button onClick={onNavigateQuiz} className="mt-5 inline-flex items-center gap-2 rounded-lg border border-[#dce7d6] bg-white px-3 py-2 text-xs font-bold text-forest">Diagnostic quiz generated <ArrowRight size={14} /></button>
        </div> : <EmptyState icon={<CalendarDays size={21} />} title="A plan that fits your life" description="Tell us what you’re studying, your exam date and your available hours. The Research, Planner, Tutor and Quiz agents will collaborate on a plan grounded in your PDFs." />}
      </section>
    </div>
  </div>;
}
