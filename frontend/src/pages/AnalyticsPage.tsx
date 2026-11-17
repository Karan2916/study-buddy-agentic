import { FormEvent, useState } from "react";
import { AlertCircle, ArrowRight, BookOpenText, LoaderCircle, Sparkles, Target, TrendingUp } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import CitationList from "../components/CitationList";
import EmptyState from "../components/EmptyState";
import type { Citation, QuizResult } from "../types";
import { api } from "../services/api";

interface Performance {
  quiz_count: number;
  average_score: number;
  topic_scores: Record<string, number>;
  strong_topics: string[];
  weak_topics: string[];
  recommendations: string[];
  history: QuizResult[];
}

export default function AnalyticsPage({ performance }: { performance: Performance }) {
  const [subject, setSubject] = useState("DBMS");
  const [gaps, setGaps] = useState<Awaited<ReturnType<typeof api.knowledgeGaps>> | null>(null);
  const [kit, setKit] = useState<{ kit: Record<string, string[]>; citations: Citation[] } | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  async function inspect(event: FormEvent) {
    event.preventDefault(); setBusy("gaps"); setError("");
    try { setGaps(await api.knowledgeGaps(subject)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Knowledge gap analysis failed."); }
    finally { setBusy(""); }
  }
  async function makeKit() {
    setBusy("kit"); setError("");
    try { setKit(await api.revisionKit(subject, "")); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Revision kit generation failed."); }
    finally { setBusy(""); }
  }
  const topics = Object.entries(performance.topic_scores).map(([topic, score]) => ({ topic, score: Math.round(score) }));
  return <div className="animate-fade-in">
    <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-3">
      <div className="rounded-2xl border border-line bg-white p-5 shadow-card"><div className="mb-4 grid h-8 w-8 place-items-center rounded-lg bg-[#eef4ea] text-forest"><TrendingUp size={16} /></div><p className="text-[10px] font-bold text-muted">OVERALL QUIZ AVERAGE</p><p className="mt-1 font-display text-3xl font-bold">{performance.quiz_count ? `${Math.round(performance.average_score)}%` : "—"}</p><p className="mt-1 text-[10px] text-muted">{performance.quiz_count} completed {performance.quiz_count === 1 ? "quiz" : "quizzes"}</p></div>
      <div className="rounded-2xl border border-line bg-white p-5 shadow-card"><div className="mb-4 grid h-8 w-8 place-items-center rounded-lg bg-[#f3f7de] text-[#728532]"><Target size={16} /></div><p className="text-[10px] font-bold text-muted">TOPICS TRACKED</p><p className="mt-1 font-display text-3xl font-bold">{topics.length}</p><p className="mt-1 text-[10px] text-muted">Across your local learning history</p></div>
      <div className="col-span-2 rounded-2xl border border-line bg-white p-5 shadow-card lg:col-span-1"><div className="mb-4 grid h-8 w-8 place-items-center rounded-lg bg-[#fff0e8] text-[#b26b41]"><AlertCircle size={16} /></div><p className="text-[10px] font-bold text-muted">NEEDS A LITTLE ATTENTION</p><p className="mt-1 font-display text-3xl font-bold">{performance.weak_topics.length}</p><p className="mt-1 text-[10px] text-muted">Topics currently below 60%</p></div>
    </div>
    <div className="grid gap-5 xl:grid-cols-[1.2fr_.8fr]">
      <section className="rounded-2xl border border-line bg-white p-5 shadow-card sm:p-6"><p className="text-[10px] font-bold uppercase tracking-[.15em] text-muted">TOPIC MASTERY</p><h2 className="mt-1 font-display text-lg font-bold">Where you stand</h2>
        {topics.length ? <div className="mt-5 h-[290px]"><ResponsiveContainer width="100%" height="100%"><BarChart data={topics} layout="vertical" margin={{ left: 10, right: 12, top: 3, bottom: 3 }}><CartesianGrid stroke="#eef0ec" horizontal={false} /><XAxis type="number" domain={[0, 100]} tick={{ fill: "#929c95", fontSize: 10 }} axisLine={false} tickLine={false} /><YAxis type="category" dataKey="topic" width={120} tick={{ fill: "#64716a", fontSize: 10 }} axisLine={false} tickLine={false} /><Tooltip formatter={(value) => [`${value}%`, "Score"]} contentStyle={{ borderRadius: 12, border: "1px solid #e7ebe4", fontSize: 12 }} /><Bar dataKey="score" radius={[0, 6, 6, 0]} barSize={20}>{topics.map((entry) => <Cell key={entry.topic} fill={entry.score >= 75 ? "#7fa875" : entry.score < 60 ? "#dba27f" : "#b7c98a"} />)}</Bar></BarChart></ResponsiveContainer></div> : <div className="grid h-64 place-items-center"><EmptyState icon={<Target size={20} />} title="Learning takes time" description="Your topic-wise insights will appear after your first quiz." /></div>}
      </section>
      <section className="rounded-2xl border border-line bg-white p-5 shadow-card sm:p-6"><p className="text-[10px] font-bold uppercase tracking-[.15em] text-muted">PERSONALIZED NEXT STEPS</p><h2 className="mt-1 font-display text-lg font-bold">A little direction</h2>
        {performance.recommendations.length ? <div className="mt-5 space-y-3">{performance.recommendations.map((item, index) => <div key={index} className="flex gap-3 rounded-xl bg-[#fff9f5] p-3"><span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-white text-[#b26b41]"><ArrowRight size={13} /></span><p className="text-xs leading-5 text-[#59665f]">{item}</p></div>)}</div> : <p className="mt-4 rounded-xl bg-[#f3f7ef] p-4 text-xs leading-5 text-muted">Complete a quiz and your Performance Agent will offer suggestions that fit your results.</p>}
      </section>
    </div>

    <section className="mt-5 rounded-2xl border border-line bg-white p-5 shadow-card sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-[10px] font-bold uppercase tracking-[.15em] text-forest">LEARNING DIAGNOSTICS</p><h2 className="mt-1 font-display text-lg font-bold">Find your next focus</h2><p className="mt-1 text-xs text-muted">Compare PDF topics with your quiz history, or build a cited revision kit.</p></div>
        <form onSubmit={(event) => void inspect(event)} className="flex flex-wrap gap-2"><input value={subject} onChange={(e) => setSubject(e.target.value)} aria-label="Subject" className="w-32 rounded-lg border border-line px-3 py-2 text-xs outline-none focus:border-[#9bb399]" /><button disabled={Boolean(busy)} className="inline-flex items-center gap-2 rounded-lg bg-forest px-3 py-2 text-xs font-bold text-white disabled:opacity-50">{busy === "gaps" ? <LoaderCircle size={13} className="animate-spin" /> : <Sparkles size={13} />}Detect knowledge gaps</button><button type="button" disabled={Boolean(busy)} onClick={() => void makeKit()} className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-xs font-bold text-forest disabled:opacity-50">{busy === "kit" ? <LoaderCircle size={13} className="animate-spin" /> : <BookOpenText size={13} />}Revision kit</button></form>
      </div>
      {error && <p className="mt-4 rounded-lg bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
      {gaps && <div className="mt-5 rounded-xl bg-canvas p-4"><p className="text-xs font-bold">Topics identified in course material</p><p className="mt-2 text-xs leading-6 text-muted">{gaps.topics_in_material.join(" · ") || "No topics were extracted."}</p><div className="mt-3 flex flex-wrap gap-2">{gaps.recommendations.map((item) => <span key={item.topic} className={`rounded-full px-3 py-1.5 text-[10px] font-semibold ${item.priority === "high" ? "bg-[#fff0e8] text-[#9c5838]" : "bg-white text-muted"}`}>{item.topic} · {item.reason}</span>)}</div><CitationList citations={gaps.citations} /></div>}
      {kit && <div className="mt-5 grid gap-3 sm:grid-cols-2">{Object.entries(kit.kit).map(([section, entries]) => <div key={section} className="rounded-xl bg-canvas p-4"><h3 className="text-xs font-bold capitalize">{section.replace(/_/g, " ")}</h3><ul className="mt-2 space-y-1.5">{entries.map((item, index) => <li key={index} className="text-xs leading-5 text-muted">{item}</li>)}</ul></div>)}<div className="sm:col-span-2"><CitationList citations={kit.citations} /></div></div>}
    </section>
  </div>;
}
