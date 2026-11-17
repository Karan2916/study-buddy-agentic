import { BookOpenText } from "lucide-react";
import type { Citation } from "../types";

export default function CitationList({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;
  return <div className="mt-4 flex flex-wrap gap-2">{citations.map((citation) =>
    <span key={`${citation.document_id}-${citation.page}`} className="inline-flex items-center gap-1.5 rounded-lg border border-[#dce7d6] bg-[#f3f8f0] px-2.5 py-1.5 text-[10px] font-semibold text-forest">
      <BookOpenText size={12} />{citation.document_name} · p. {citation.page}
    </span>)}</div>;
}
