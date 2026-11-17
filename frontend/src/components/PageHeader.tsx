import { Bell, Search, Sparkles } from "lucide-react";
import type { Section } from "../types";

const title: Record<Section, { eyebrow: string; name: string; description: string }> = {
  dashboard: { eyebrow: "YOUR LEARNING SPACE", name: "Good to see you.", description: "A clear view of your learning, all in one place." },
  chat: { eyebrow: "YOUR AI TUTOR", name: "Study chat", description: "Ask anything. Your course materials stay at the center." },
  documents: { eyebrow: "YOUR KNOWLEDGE BASE", name: "My materials", description: "Your PDFs become searchable, page-cited study knowledge." },
  planner: { eyebrow: "MAKE A PLAN", name: "Study planner", description: "A thoughtful plan built around your exam and your time." },
  quiz: { eyebrow: "PRACTICE & GROW", name: "Quiz center", description: "Test what you know, then learn from every answer." },
  analytics: { eyebrow: "YOUR PROGRESS", name: "Performance", description: "Notice your strengths. Spend time where it matters." },
  activity: { eyebrow: "BEHIND THE SCENES", name: "Agent activity", description: "See what your specialist learning agents actually do." },
};

export default function PageHeader({ section, llmConfigured }: { section: Section; llmConfigured: boolean }) {
  const page = title[section];
  return (
    <header className="mb-8 flex flex-wrap items-start justify-between gap-5">
      <div><p className="mb-2 text-[10px] font-bold tracking-[.18em] text-forest">{page.eyebrow}</p><h1 className="font-display text-[32px] font-bold tracking-[-.045em] text-ink sm:text-[38px]">{page.name}</h1><p className="mt-1.5 text-[13px] text-muted">{page.description}</p></div>
      <div className="flex items-center gap-2">
        <div className={`flex items-center gap-2 rounded-full border px-3 py-2 text-[11px] font-semibold ${llmConfigured ? "border-[#dfe8dc] bg-white text-forest" : "border-amber-200 bg-amber-50 text-amber-800"}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${llmConfigured ? "bg-emerald-500" : "bg-amber-500"}`} />
          {llmConfigured ? "AI ready" : "Add API settings"}
        </div>
        <button aria-label="Search" className="hidden h-9 w-9 place-items-center rounded-xl border border-line bg-white text-muted sm:grid"><Search size={16} /></button>
        <button aria-label="AI status" className="grid h-9 w-9 place-items-center rounded-xl border border-line bg-white text-muted"><Bell size={16} /></button>
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-forest text-lime"><Sparkles size={16} /></div>
      </div>
    </header>
  );
}
