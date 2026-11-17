import type { ReactNode } from "react";

export default function MetricCard({ label, value, note, icon, accent = "green" }: {
  label: string; value: string | number; note: string; icon: ReactNode; accent?: "green" | "lime" | "peach" | "blue";
}) {
  const color: Record<string, string> = {
    green: "bg-[#eaf2e8] text-forest", lime: "bg-[#f3f7de] text-[#6d7f25]",
    peach: "bg-[#fff0e8] text-[#b26b41]", blue: "bg-[#eaf1f5] text-[#567c8c]",
  };
  return (
    <div className="rounded-2xl border border-line bg-white p-5 shadow-card transition-transform hover:-translate-y-0.5">
      <div className="mb-5 flex items-center justify-between"><p className="text-[11px] font-bold text-muted">{label}</p><div className={`grid h-8 w-8 place-items-center rounded-lg ${color[accent]}`}>{icon}</div></div>
      <p className="font-display text-[28px] font-bold tracking-tight text-ink">{value}</p><p className="mt-1 text-[10px] text-muted">{note}</p>
    </div>
  );
}
