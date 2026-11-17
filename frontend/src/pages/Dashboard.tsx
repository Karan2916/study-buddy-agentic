import { ArrowDownRight, ArrowRight, ArrowUpRight, BookOpen, BrainCircuit, FileText, Flame, Sparkles } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import MetricCard from "../components/MetricCard";
import type { ActivityEvent, DocumentItem, Section, StudyPlan } from "../types";

interface Props {
  documents: DocumentItem[];
  plan: StudyPlan | null;
  performance: { quiz_count: number; average_score: number; topic_scores: Record<string, number>; history: { score_percent: number; created_at?: string }[] };
  activity: ActivityEvent[];
  onNavigate: (section: Section) => void;
}

export default function Dashboard({ documents, plan, performance, activity, onNavigate }: Props) {
  const chartData = performance.history.slice(-7).map((item, index) => ({
    name: `Quiz ${index + 1}`,
    score: item.score_percent,
  }));
  const weak = Object.entries(performance.topic_scores).filter(([, score]) => score < 60).slice(0, 3);
  const strong = Object.entries(performance.topic_scores).filter(([, score]) => score >= 75).slice(0, 3);
  const strongCount = Object.values(performance.topic_scores).filter((score) => score >= 75).length;
  return <div className="animate-fade-in">
    <section className="relative mb-6 overflow-hidden rounded-[24px] bg-forest p-7 text-white sm:p-9">
      <div className="noise absolute inset-0 opacity-30" /><div className="absolute -right-10 -top-20 h-64 w-64 rounded-full border border-white/10" /><div className="absolute -right-1 top-4 h-44 w-44 rounded-full border border-white/10" />
      <div className="relative max-w-[600px]">
        <div className="mb-4 inline-flex items-center gap-1.5 rounded-full border border-white/20 bg-white/10 px-2.5 py-1 text-[10px] font-semibold text-lime"><Sparkles size={12} /> YOUR AI LEARNING COMPANION</div>
        <h2 className="font-display text-[27px] font-bold leading-tight tracking-[-.035em] sm:text-[34px]">Small steps. <span className="text-lime">Big understanding.</span></h2>
        <p className="mt-2 max-w-md text-sm leading-6 text-white/70">Your study space is ready when you are. Ask questions, make a plan, or try a quick quiz on what you’ve learned.</p>
        <div className="mt-6 flex flex-wrap gap-2"><button onClick={() => onNavigate("chat")} className="inline-flex items-center gap-2 rounded-xl bg-lime px-4 py-2.5 text-xs font-bold text-forest transition-transform hover:scale-[1.02]">Start studying <ArrowRight size={14} /></button><button onClick={() => onNavigate("documents")} className="rounded-xl border border-white/20 px-4 py-2.5 text-xs font-semibold text-white/90 hover:bg-white/10">Add a course PDF</button></div>
      </div>
      <div className="absolute bottom-8 right-[12%] hidden h-20 w-20 rotate-[-8deg] items-center justify-center rounded-[22px] border border-white/20 bg-white/10 backdrop-blur md:flex"><BookOpen size={29} className="text-lime" /><span className="absolute -right-2 -top-2 grid h-7 w-7 place-items-center rounded-lg bg-lime text-forest"><Sparkles size={13} /></span></div>
    </section>

    <div className="mb-6 grid grid-cols-2 gap-3 xl:grid-cols-4">
      <MetricCard label="COURSE MATERIALS" value={documents.length} note={`${documents.reduce((n, d) => n + d.pages, 0)} pages ready to explore`} icon={<FileText size={16} />} />
      <MetricCard label="QUIZZES COMPLETED" value={performance.quiz_count} note="Every attempt helps you grow" icon={<BrainCircuit size={16} />} accent="lime" />
      <MetricCard label="AVERAGE SCORE" value={performance.quiz_count ? `${Math.round(performance.average_score)}%` : "—"} note={performance.quiz_count ? "Across all completed quizzes" : "Your first quiz starts here"} icon={<ArrowUpRight size={16} />} accent="peach" />
      <MetricCard label="TOPICS MASTERED" value={strongCount} note="Scoring 75% or higher" icon={<Flame size={16} />} accent="blue" />
    </div>

    <div className="grid gap-5 xl:grid-cols-[1.35fr_.85fr]">
      <section className="rounded-2xl border border-line bg-white p-5 shadow-card sm:p-6">
        <div className="mb-5 flex items-center justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.15em] text-muted">LEARNING MOMENTUM</p><h3 className="mt-1 font-display text-lg font-bold">Your quiz scores</h3></div><button onClick={() => onNavigate("analytics")} className="text-xs font-bold text-forest">See insights <ArrowRight size={13} className="ml-1 inline" /></button></div>
        {chartData.length ? <div className="h-[210px] w-full">
          <ResponsiveContainer width="100%" height="100%"><AreaChart data={chartData} margin={{ left: -20, right: 8, top: 10 }}>
            <defs><linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#79a889" stopOpacity={0.28} /><stop offset="95%" stopColor="#79a889" stopOpacity={0.01} /></linearGradient></defs>
            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: "#929c95", fontSize: 10 }} />
            <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e7ebe4", fontSize: 12 }} formatter={(value) => [`${value}%`, "Score"]} />
            <Area type="monotone" dataKey="score" stroke="#1d5948" strokeWidth={2.5} fill="url(#scoreFill)" dot={{ fill: "#d8f06b", stroke: "#1d5948", strokeWidth: 2, r: 4 }} activeDot={{ r: 6 }} />
          </AreaChart></ResponsiveContainer>
        </div> : <div className="grid h-[200px] place-items-center text-center"><div><div className="mx-auto mb-2 grid h-10 w-10 place-items-center rounded-full bg-[#f2f5eb] text-forest"><BrainCircuit size={18} /></div><p className="text-sm font-bold">Your progress will take shape here</p><p className="mt-1 text-xs text-muted">Complete your first quiz to start tracking.</p></div></div>}
      </section>
      <section className="rounded-2xl border border-line bg-white p-5 shadow-card sm:p-6">
        <div className="mb-5 flex items-center justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.15em] text-muted">YOUR NEXT MILESTONE</p><h3 className="mt-1 font-display text-lg font-bold">Study plan</h3></div><button onClick={() => onNavigate("planner")} className="grid h-8 w-8 place-items-center rounded-lg bg-canvas text-muted hover:text-forest"><ArrowRight size={15} /></button></div>
        {plan ? <><div className="rounded-xl bg-[#f3f7ef] p-4"><div className="flex items-start justify-between gap-3"><div><p className="font-bold">{plan.title}</p><p className="mt-1 text-xs text-muted">Exam · {plan.exam_date} · {plan.hours_per_day}h/day</p></div><span className="rounded-full bg-white px-2.5 py-1 text-[10px] font-bold text-forest">{plan.sessions.length} days</span></div><p className="mt-4 text-[10px] text-muted">Your plan is ready to follow</p></div><button onClick={() => onNavigate("planner")} className="mt-4 text-xs font-bold text-forest">Open your plan <ArrowRight size={13} className="ml-1 inline" /></button></> :
          <div className="rounded-xl border border-dashed border-line p-5 text-center"><p className="text-sm font-semibold">No plan yet. That’s a good place to start.</p><p className="mt-1 text-xs text-muted">Set a goal and your AI planner will map the way.</p><button onClick={() => onNavigate("planner")} className="mt-3 rounded-lg bg-forest px-3 py-2 text-xs font-bold text-white">Create a study plan</button></div>}
      </section>
    </div>

    <div className="mt-5 grid gap-5 lg:grid-cols-[.8fr_1.2fr]">
      <section className="rounded-2xl border border-line bg-white p-5 shadow-card">
        <div className="mb-4 flex items-center justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.15em] text-muted">TOPIC CHECK-IN</p><h3 className="mt-1 font-display text-base font-bold">You’re doing well at</h3></div><span className="grid h-8 w-8 place-items-center rounded-lg bg-[#f3f7de] text-[#728532]"><ArrowUpRight size={16} /></span></div>
        {strong.length ? <div className="space-y-3">{strong.map(([topic, score]) => <div key={topic}><div className="mb-1.5 flex justify-between text-xs"><span className="font-semibold">{topic}</span><span className="font-mono text-muted">{Math.round(score)}%</span></div><div className="h-1.5 overflow-hidden rounded-full bg-canvas"><div className="h-full rounded-full bg-[#87aa75]" style={{ width: `${score}%` }} /></div></div>)}</div> : <p className="text-xs leading-5 text-muted">Your strongest topics appear after you complete quizzes.</p>}
      </section>
      <section className="rounded-2xl border border-line bg-white p-5 shadow-card">
        <div className="mb-4 flex items-center justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.15em] text-muted">RECENT ACTIVITY</p><h3 className="mt-1 font-display text-base font-bold">Your learning, lately</h3></div><button onClick={() => onNavigate("activity")} className="text-xs font-bold text-forest">All activity</button></div>
        {activity.length ? <div className="space-y-3">{activity.slice(0, 3).map((item) => <div key={item.id} className="flex gap-3"><div className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-forest" /><div className="min-w-0 flex-1"><div className="flex flex-wrap justify-between gap-2"><p className="text-xs font-bold">{item.agent}</p><time className="text-[10px] text-muted">{new Date(item.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time></div><p className="mt-0.5 truncate text-xs text-muted">{item.message}</p></div></div>)}</div> : <div className="flex items-center gap-3 py-2 text-xs text-muted"><Sparkles size={16} className="text-forest" />Agent activity appears as you study.</div>}
      </section>
    </div>
    {weak.length > 0 && <button onClick={() => onNavigate("analytics")} className="mt-5 flex w-full items-center gap-3 rounded-xl border border-[#f1e4dc] bg-[#fff9f5] p-4 text-left"><span className="grid h-8 w-8 place-items-center rounded-lg bg-[#ffede2] text-[#b26b41]"><ArrowDownRight size={15} /></span><span className="flex-1"><span className="block text-xs font-bold">A little more practice could help</span><span className="mt-0.5 block text-[11px] text-muted">{weak.map(([topic]) => topic).join(", ")} · Your study plan can adapt around these.</span></span><ArrowRight size={14} className="text-muted" /></button>}
  </div>;
}
