import { AlertCircle, CheckCircle2, X } from "lucide-react";

export default function Notice({ message, onDismiss }: { message: string; onDismiss?: () => void }) {
  if (!message) return null;
  const isError = /error|failed|unable|could not|not configured|upload a/i.test(message);
  const Icon = isError ? AlertCircle : CheckCircle2;
  return (
    <div className={`mb-5 flex items-start gap-2 rounded-xl border px-4 py-3 text-sm ${isError ? "border-rose-100 bg-rose-50 text-rose-800" : "border-emerald-100 bg-emerald-50 text-emerald-800"}`}>
      <Icon className="mt-0.5 shrink-0" size={16} /><p className="flex-1">{message}</p>
      {onDismiss && <button aria-label="Dismiss" onClick={onDismiss}><X size={15} /></button>}
    </div>
  );
}
