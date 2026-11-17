import { FormEvent, useState } from "react";
import { ArrowUp, BookOpenText, Bot, LoaderCircle, Sparkles, UserRound } from "lucide-react";
import CitationList from "../components/CitationList";
import EmptyState from "../components/EmptyState";
import type { Citation, Quiz, StudyPlan } from "../types";
import { api } from "../services/api";

interface Message { role: "user" | "assistant"; text: string; agents?: string[]; citations?: Citation[]; quiz?: Quiz; plan?: StudyPlan; }

export default function ChatPage({ hasDocuments, onQuiz, onPlan }: { hasDocuments: boolean; onQuiz: (quiz: Quiz) => void; onPlan: (plan: StudyPlan) => void }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState("simple");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  async function send(event?: FormEvent, prompt?: string) {
    event?.preventDefault();
    const text = (prompt ?? input).trim();
    if (!text || sending) return;
    setInput(""); setError(""); setMessages((items) => [...items, { role: "user", text }]); setSending(true);
    try {
      const response = await api.chat(text, mode);
      setMessages((items) => [...items, { role: "assistant", text: response.answer, agents: response.agents, citations: response.citations, quiz: response.quiz, plan: response.plan }]);
      if (response.quiz) onQuiz(response.quiz);
      if (response.plan) onPlan(response.plan);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "The AI request failed."); }
    finally { setSending(false); }
  }
  return <div className="animate-fade-in">
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#e5ebe2] bg-white px-4 py-3">
      <div className="flex items-center gap-2 text-xs"><span className={`h-2 w-2 rounded-full ${hasDocuments ? "bg-emerald-500" : "bg-amber-500"}`} /><span className="font-semibold">{hasDocuments ? "Grounded in your course library" : "No course PDFs indexed"}</span><span className="hidden text-muted sm:inline">{hasDocuments ? "Page citations appear with sourced answers." : "Upload a PDF for course-grounded answers."}</span></div>
      <select aria-label="Explanation style" value={mode} onChange={(e) => setMode(e.target.value)} className="rounded-lg border border-line bg-canvas px-2.5 py-1.5 text-[11px] font-semibold outline-none focus:border-forest"><option value="simple">Simple explanation</option><option value="detailed">Detailed steps</option><option value="examples">With examples</option><option value="exam">Exam-oriented</option></select>
    </div>
    <div className="flex min-h-[430px] flex-col rounded-2xl border border-line bg-white shadow-card">
      <div className="scrollbar-thin flex-1 space-y-5 overflow-y-auto p-4 sm:p-6">
        {!messages.length && <EmptyState icon={<Bot size={21} />} title="What are you working on?" description="Ask a question, explore a tricky concept, or tell your study team what you need to prepare." />}
        {messages.map((message, index) => <div key={index} className={`flex gap-3 ${message.role === "user" ? "justify-end" : ""}`}>
          {message.role === "assistant" && <div className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-forest text-lime"><Sparkles size={15} /></div>}
          <div className={`max-w-[88%] rounded-2xl px-4 py-3 ${message.role === "user" ? "bg-[#eef4ea] text-ink" : "bg-canvas text-ink"}`}>
            {message.role === "assistant" ? <div className="prose-study whitespace-pre-wrap text-[13px] leading-6">{message.text}</div> : <p className="whitespace-pre-wrap text-[13px] leading-6">{message.text}</p>}
            {message.role === "assistant" && <>
              {message.agents && message.agents.length > 0 && <div className="mt-3 flex flex-wrap gap-1.5">{message.agents.map((agent) => <span key={agent} className="rounded-md border border-[#e0e8dc] bg-white px-2 py-1 text-[9px] font-bold uppercase tracking-wide text-forest">{agent}</span>)}</div>}
              <CitationList citations={message.citations ?? []} />
              {message.quiz && <button onClick={() => onQuiz(message.quiz!)} className="mt-3 flex items-center gap-2 rounded-lg bg-forest px-3 py-2 text-xs font-bold text-white"><BookOpenText size={14} /> Open generated diagnostic quiz</button>}
              {message.plan && <p className="mt-3 text-xs font-semibold text-forest">Study plan created: {message.plan.title}</p>}
            </>}
          </div>
          {message.role === "user" && <div className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-[#e6e9e4] text-[#6d7972]"><UserRound size={15} /></div>}
        </div>)}
        {sending && <div className="flex items-center gap-3"><div className="grid h-8 w-8 place-items-center rounded-xl bg-forest text-lime"><Sparkles size={15} /></div><div className="flex items-center gap-2 rounded-2xl bg-canvas px-4 py-3 text-xs text-muted"><LoaderCircle size={14} className="animate-spin" />Your agents are collaborating…</div></div>}
        {error && <div className="rounded-xl bg-rose-50 px-4 py-3 text-xs text-rose-700">{error}</div>}
      </div>
      <form onSubmit={(event) => void send(event)} className="border-t border-line p-3 sm:p-4">
        {!messages.length && <div className="mb-3 flex flex-wrap gap-2"><button type="button" onClick={() => void send(undefined, "Explain the most important concepts in my course material")} className="rounded-full border border-line px-3 py-1.5 text-[10px] font-semibold text-muted hover:border-[#c5d5c1] hover:text-forest">Explain key concepts</button><button type="button" onClick={() => void send(undefined, "Make me a quiz from my uploaded study materials")} className="rounded-full border border-line px-3 py-1.5 text-[10px] font-semibold text-muted hover:border-[#c5d5c1] hover:text-forest">Quiz me</button><button type="button" onClick={() => void send(undefined, "Help me prepare for an exam")} className="rounded-full border border-line px-3 py-1.5 text-[10px] font-semibold text-muted hover:border-[#c5d5c1] hover:text-forest">Exam prep</button></div>}
        <div className="flex items-end gap-3 rounded-xl border border-line bg-white px-3 py-2 focus-within:border-[#aabda6]"><textarea rows={1} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void send(); } }} placeholder="Ask your study buddy anything…" className="max-h-28 min-h-9 flex-1 resize-y border-0 bg-transparent py-2 text-sm outline-none placeholder:text-[#a3aaa5]" /><button aria-label="Send message" disabled={!input.trim() || sending} className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-forest text-white transition-colors hover:bg-[#174b3d] disabled:bg-[#dfe4dc] disabled:text-muted"><ArrowUp size={17} /></button></div>
        <p className="mt-2 text-center text-[9px] text-muted">Your course PDFs are the source of truth. Answers show citations when available.</p>
      </form>
    </div>
  </div>;
}
