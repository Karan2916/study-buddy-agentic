import { Activity, CheckCircle2, CircleAlert, LoaderCircle, Radio, Sparkles } from "lucide-react";
import type { ActivityEvent } from "../types";

const colors: Record<string, string> = {
  "Orchestrator Agent": "bg-[#eaf2e8] text-forest",
  "Research Agent": "bg-[#eaf1f5] text-[#567c8c]",
  "Tutor Agent": "bg-[#f3f7de] text-[#728532]",
  "Quiz Agent": "bg-[#fff0e8] text-[#b26b41]",
  "Study Planner Agent": "bg-[#edf0fa] text-[#6572a2]",
  "Performance Agent": "bg-[#f8edf3] text-[#a26282]",
};

export default function ActivityPage({ events }: { events: ActivityEvent[] }) {
  return <div className="animate-fade-in">
    <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#dfe8dc] bg-[#eef4ea] p-5"><div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-xl bg-white text-forest"><Radio size={18} /></div><div><h2 className="font-display text-base font-bold">Live agent execution log</h2><p className="text-[11px] text-[#65776a]">These events are recorded by the backend as real agents run. Refreshes automatically.</p></div></div><span className="flex items-center gap-1.5 rounded-full bg-white px-3 py-1.5 text-[10px] font-bold text-forest"><span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" /> POLLING</span></div>
    {events.length ? <div className="relative ml-4 border-l border-[#dce4d9] pl-7">{events.map((event) => {
      const Icon = event.status === "error" ? CircleAlert : event.status === "routing" ? Activity : CheckCircle2;
      return <article key={event.id} className="relative mb-4 rounded-2xl border border-line bg-white p-4 shadow-card sm:p-5">
        <div className="absolute -left-[35px] top-5 grid h-7 w-7 place-items-center rounded-lg border border-[#e7ebe4] bg-white"><span className="h-2 w-2 rounded-full bg-forest" /></div>
        <div className="flex flex-wrap items-start justify-between gap-3"><div className="flex items-start gap-3"><div className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl ${colors[event.agent] ?? "bg-canvas text-muted"}`}><Icon size={16} /></div><div><div className="flex flex-wrap items-center gap-2"><h3 className="text-xs font-bold">{event.agent}</h3><span className={`rounded-md px-1.5 py-0.5 text-[9px] font-bold uppercase ${event.status === "error" ? "bg-rose-50 text-rose-700" : event.status === "routing" ? "bg-[#f3f7de] text-[#728532]" : "bg-[#edf6ed] text-emerald-700"}`}>{event.status}</span></div><p className="mt-1 text-xs leading-5 text-[#59665f]">{event.message}</p>{event.details && <p className="mt-2 rounded-lg bg-canvas p-2.5 text-[10px] leading-5 text-muted">{event.details}</p>}</div></div><time className="whitespace-nowrap text-[10px] text-muted">{new Date(event.created_at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" })}</time></div>
      </article>;
    })}</div> : <div className="grid min-h-64 place-items-center rounded-2xl border border-dashed border-line bg-white"><div className="text-center"><div className="mx-auto mb-3 grid h-11 w-11 place-items-center rounded-xl bg-[#eef4ea] text-forest"><Sparkles size={20} /></div><p className="text-sm font-bold">Your agents are standing by</p><p className="mt-1 text-xs text-muted">Start a chat or generate a study plan to see real workflow events here.</p></div></div>}
    <div className="mt-5 flex items-center gap-2 text-[10px] text-muted"><LoaderCircle size={12} /> Activity is persisted locally and refreshed every few seconds.</div>
  </div>;
}
