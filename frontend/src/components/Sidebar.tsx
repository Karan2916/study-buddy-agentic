import {
  Activity, BookOpen, BrainCircuit, CalendarDays, ChartNoAxesCombined, FileText,
  GraduationCap, LayoutDashboard, MessageCircle, PanelLeftClose, PanelLeftOpen,
} from "lucide-react";
import type { Section } from "../types";

const links: { id: Section; label: string; icon: typeof LayoutDashboard; group: string }[] = [
  { id: "dashboard", label: "Overview", icon: LayoutDashboard, group: "Workspace" },
  { id: "chat", label: "AI study chat", icon: MessageCircle, group: "Workspace" },
  { id: "documents", label: "My materials", icon: FileText, group: "Workspace" },
  { id: "planner", label: "Study planner", icon: CalendarDays, group: "Learn" },
  { id: "quiz", label: "Quiz center", icon: BrainCircuit, group: "Learn" },
  { id: "analytics", label: "Performance", icon: ChartNoAxesCombined, group: "Learn" },
  { id: "activity", label: "Agent activity", icon: Activity, group: "System" },
];

interface Props {
  active: Section;
  onChange: (section: Section) => void;
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({ active, onChange, collapsed, onToggle }: Props) {
  return (
    <aside className={`fixed inset-y-0 left-0 z-30 flex flex-col border-r border-line bg-white transition-all duration-200 ${collapsed ? "w-[76px]" : "w-[248px]"}`}>
      <div className={`flex h-[76px] items-center border-b border-line ${collapsed ? "justify-center" : "gap-3 px-6"}`}>
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-forest text-lime"><GraduationCap size={20} /></div>
        {!collapsed && <div><p className="font-display text-[15px] font-extrabold tracking-tight">study buddy<span className="text-forest">.</span></p><p className="text-[10px] font-semibold uppercase tracking-[.17em] text-muted">your AI workspace</p></div>}
      </div>
      <nav className="scrollbar-thin flex-1 overflow-y-auto px-3 py-6">
        {["Workspace", "Learn", "System"].map((group) => (
          <div className="mb-6" key={group}>
            {!collapsed && <p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[.16em] text-[#a2aaa3]">{group}</p>}
            {links.filter((link) => link.group === group).map(({ id, label, icon: Icon }) => (
              <button key={id} onClick={() => onChange(id)} title={collapsed ? label : undefined}
                className={`mb-1 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[13px] font-semibold transition-colors ${collapsed ? "justify-center" : ""} ${active === id ? "bg-[#eef4ea] text-forest" : "text-[#65716b] hover:bg-canvas hover:text-ink"}`}>
                <Icon size={17} strokeWidth={active === id ? 2.2 : 1.8} />{!collapsed && label}
              </button>
            ))}
          </div>
        ))}
      </nav>
      <div className="border-t border-line p-3">
        <button onClick={onToggle} className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-xs font-semibold text-muted hover:bg-canvas ${collapsed ? "justify-center" : ""}`}>
          {collapsed ? <PanelLeftOpen size={16} /> : <><PanelLeftClose size={16} /> Collapse sidebar</>}
        </button>
        {!collapsed && <div className="mt-4 flex items-center gap-3 rounded-xl bg-canvas p-3"><div className="grid h-8 w-8 place-items-center rounded-full bg-lime text-forest"><BookOpen size={15} /></div><div className="min-w-0"><p className="truncate text-xs font-bold">Your learning space</p><p className="text-[10px] text-muted">Private · stored locally</p></div></div>}
      </div>
    </aside>
  );
}
