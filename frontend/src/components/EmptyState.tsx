import type { ReactNode } from "react";

export default function EmptyState({ icon, title, description, action }: { icon: ReactNode; title: string; description: string; action?: ReactNode }) {
  return <div className="grid min-h-56 place-items-center rounded-2xl border border-dashed border-[#dce3da] bg-white/70 p-8 text-center">
    <div><div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-2xl bg-[#eef4ea] text-forest">{icon}</div><h3 className="font-display text-lg font-bold">{title}</h3><p className="mx-auto mt-1.5 max-w-sm text-sm leading-6 text-muted">{description}</p>{action && <div className="mt-4">{action}</div>}</div>
  </div>;
}
