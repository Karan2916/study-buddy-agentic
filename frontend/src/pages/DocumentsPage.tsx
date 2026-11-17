import { useRef, useState } from "react";
import { BookOpen, FileText, LoaderCircle, Plus, Trash2, UploadCloud } from "lucide-react";
import EmptyState from "../components/EmptyState";
import type { DocumentItem } from "../types";
import { api } from "../services/api";

export default function DocumentsPage({ documents, onRefresh, notify }: { documents: DocumentItem[]; onRefresh: () => Promise<void>; notify: (message: string) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  async function upload(file?: File) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) { notify("Please choose a PDF file."); return; }
    setBusy(true);
    try { await api.upload(file); await onRefresh(); notify(`${file.name} was extracted and indexed successfully.`); }
    catch (error) { notify(error instanceof Error ? error.message : "PDF upload failed."); }
    finally { setBusy(false); if (inputRef.current) inputRef.current.value = ""; }
  }
  async function remove(document: DocumentItem) {
    if (!window.confirm(`Delete “${document.name}” and rebuild the local search index?`)) return;
    setDeleting(document.id);
    try { await api.deleteDocument(document.id); await onRefresh(); notify(`${document.name} was removed.`); }
    catch (error) { notify(error instanceof Error ? error.message : "Document deletion failed."); }
    finally { setDeleting(null); }
  }
  return <div className="animate-fade-in">
    <div className="mb-6 rounded-2xl border border-[#dfe8dc] bg-[#eef4ea] p-5 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-4"><div className="flex items-start gap-3"><div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white text-forest"><BookOpen size={19} /></div><div><h2 className="font-display text-lg font-bold">Your course library</h2><p className="mt-1 max-w-xl text-xs leading-5 text-[#65776a]">Upload text-based PDFs. Study Buddy extracts page-numbered passages, then indexes them locally for grounded answers and quizzes.</p></div></div>
        <button disabled={busy} onClick={() => inputRef.current?.click()} className="inline-flex items-center gap-2 rounded-xl bg-forest px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-[#174b3d] disabled:opacity-50">{busy ? <LoaderCircle className="animate-spin" size={15} /> : <Plus size={15} />}{busy ? "Processing PDF…" : "Add a PDF"}</button>
      </div>
      <input ref={inputRef} className="hidden" type="file" accept="application/pdf,.pdf" onChange={(event) => void upload(event.target.files?.[0])} />
      <div onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); void upload(event.dataTransfer.files[0]); }} className="mt-5 flex cursor-pointer flex-col items-center rounded-xl border border-dashed border-[#c9d8c6] bg-white/60 py-5 text-center" onClick={() => inputRef.current?.click()}>
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-white text-forest"><UploadCloud size={17} /></div><p className="mt-2 text-xs font-semibold">{busy ? "Extracting, embedding and indexing on this device" : "Drop a PDF here, or browse to choose one"}</p><p className="mt-1 text-[10px] text-muted">PDF · up to 30 MB · scanned PDFs are not OCR processed</p>
      </div>
    </div>

    <div className="mb-3 flex items-end justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.15em] text-muted">LIBRARY</p><h2 className="mt-1 font-display text-xl font-bold">{documents.length} {documents.length === 1 ? "document" : "documents"}</h2></div><p className="text-[10px] text-muted">Stored on this computer</p></div>
    {documents.length ? <div className="space-y-3">{documents.map((document) => <article key={document.id} className="flex flex-wrap items-center gap-4 rounded-2xl border border-line bg-white p-4 shadow-card sm:px-5">
      <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-[#fff0e8] text-[#bb7050]"><FileText size={19} /></div><div className="min-w-0 flex-1"><h3 className="truncate text-sm font-bold">{document.name}</h3><p className="mt-1 text-[11px] text-muted">{document.pages} pages · {document.chunks} searchable passages · {(document.size_bytes / 1024 / 1024).toFixed(1)} MB</p></div><span className="rounded-full bg-[#edf6ed] px-2.5 py-1 text-[10px] font-bold text-emerald-700">{document.status}</span><button aria-label={`Delete ${document.name}`} disabled={deleting === document.id} onClick={() => void remove(document)} className="grid h-9 w-9 place-items-center rounded-lg text-muted hover:bg-rose-50 hover:text-rose-600 disabled:opacity-50">{deleting === document.id ? <LoaderCircle className="animate-spin" size={15} /> : <Trash2 size={15} />}</button>
    </article>)}</div> : <EmptyState icon={<FileText size={21} />} title="A good place to start" description="Add a course PDF and your AI study agents can research, explain, and quiz you on its contents." action={<button onClick={() => inputRef.current?.click()} className="rounded-lg bg-forest px-4 py-2 text-xs font-bold text-white">Choose your first PDF</button>} />}
  </div>;
}
