"use client";

import { useState, useRef } from "react";
import LensScene from "../components/LensScene";
import ResearchDashboard from "../components/ResearchDashboard";
import {
  createResearchRun,
  pollResearchRun,
  fetchAllRunArtifacts,
  uploadDocument,
  type ResearchRunResult,
  type RunArtifactsBundle,
} from "../lib/api/client";

export default function Home() {
  const [idea, setIdea] = useState("");
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [uploadedDocName, setUploadedDocName] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState<string | null>(null);
  const [progressPct, setProgressPct] = useState(0);

  const [bundle, setBundle] = useState<RunArtifactsBundle | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [statusFeedback, setStatusFeedback] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);
    try {
      const doc = await uploadDocument(file);
      setDocumentId(doc.id);
      setUploadedDocName(`${doc.filename} (${doc.word_count} words)`);
      if (doc.extracted_text) {
        setIdea(doc.extracted_text.slice(0, 1500));
      }
      setStatusFeedback(`Parsed ${doc.filename}: extracted text loaded into idea box.`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to upload document";
      setUploadError(msg);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function runResearch() {
    if (idea.trim().length < 20) return;
    setLoading(true);
    setProgressMsg("INITIALIZING QUEUED RUN…");
    setProgressPct(5);
    setStatusFeedback(null);

    try {
      // 1. Create run on backend
      const initialRun: ResearchRunResult = await createResearchRun(idea.trim(), documentId);
      setIsLive(true);
      setProgressMsg(`STAGE: ${initialRun.current_stage ?? "DECOMPOSITION"}`);
      setProgressPct(initialRun.progress || 10);

      // 2. Poll until completed or failed
      const completedRun = await pollResearchRun(initialRun.id, (runUpdate) => {
        setProgressPct(runUpdate.progress);
        if (runUpdate.current_stage) {
          setProgressMsg(`STAGE: ${runUpdate.current_stage.toUpperCase().replace(/_/g, " ")} (${runUpdate.progress}%)`);
        }
      });

      setProgressMsg("FETCHING ARTIFACTS & EVIDENCE…");
      setProgressPct(96);

      // 3. Fetch all artifacts in parallel
      const liveBundle = await fetchAllRunArtifacts(completedRun);
      setBundle(liveBundle);
      setProgressPct(100);
      setStatusFeedback(`Live research completed: ${liveBundle.sources.length} sources and ${liveBundle.evidence.length} evidence items mapped.`);
    } catch (err) {
      console.warn("Backend unavailable or encountered error; falling back to demo corpus:", err);
      setIsLive(false);
      setBundle(null);
      setStatusFeedback("Backend unavailable or local demo fallback triggered — displaying simulated research corpus.");
    } finally {
      setLoading(false);
      setProgressMsg(null);
      window.setTimeout(() => {
        document.getElementById("workspace")?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    }
  }

  return (
    <main className="grid-bg min-h-screen overflow-hidden text-slate-100">
      {/* Navigation */}
      <nav className="fixed top-0 z-50 flex w-full items-center justify-between border-b border-white/5 bg-slate-950/70 px-6 py-4 backdrop-blur-md md:px-10">
        <div className="flex items-center gap-3">
          <div className="h-2.5 w-2.5 rounded-full bg-cyan-300 shadow-[0_0_18px_rgba(99,230,255,.9)]" />
          <span className="text-sm font-semibold tracking-[.25em]">IDEALENS</span>
        </div>
        <div className="hidden gap-7 text-xs font-medium tracking-wider text-slate-400 md:flex">
          <a href="#workspace" className="hover:text-cyan-300 transition">INTELLIGENCE</a>
          <a href="#how" className="hover:text-cyan-300 transition">METHOD</a>
          <a href="#workspace" className="hover:text-cyan-300 transition">TRACEABLE REPORT</a>
        </div>
        <button
          onClick={() => document.getElementById("idea-box")?.focus()}
          className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-slate-200 backdrop-blur transition hover:border-cyan-400/40 hover:bg-white/10"
        >
          START RESEARCH →
        </button>
      </nav>

      {/* Hero Section */}
      <section className="relative mx-auto flex min-h-screen max-w-7xl flex-col justify-center px-6 pt-24 md:px-10">
        <div className="grid items-center gap-8 lg:grid-cols-[1fr_1.1fr]">
          <div className="relative z-10">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/5 px-3 py-1 text-[10px] font-semibold tracking-[.3em] text-cyan-300">
              EVIDENCE-DRIVEN TECHNICAL IDEA INTELLIGENCE
            </div>
            <h1 className="max-w-4xl text-5xl font-semibold leading-[.98] tracking-[-.04em] md:text-7xl">
              SEE WHAT YOUR IDEA IS UP AGAINST.<br />
              <span className="text-slate-500">BEFORE YOU BUILD IT.</span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-slate-400">
              IdeaLens decomposes technical ideas, retrieves research and code evidence, maps overlap,
              surfaces contradictions, identifies limited-evidence areas, and synthesizes a defensible direction.
            </p>

            {/* Input Box & Document Ingestion */}
            <div className="mt-8 max-w-xl">
              <div className="glass rounded-2xl p-3 border border-white/10 shadow-2xl">
                <textarea
                  id="idea-box"
                  value={idea}
                  onChange={(e) => setIdea(e.target.value)}
                  placeholder="Describe your technical idea, hypothesis, or paste research proposal..."
                  className="h-32 w-full resize-none bg-transparent p-3 text-sm text-white outline-none placeholder:text-slate-600"
                />

                {/* Uploaded doc badge */}
                {uploadedDocName && (
                  <div className="mb-2 flex items-center justify-between rounded-lg border border-cyan-400/30 bg-cyan-400/10 px-3 py-1.5 text-xs text-cyan-200">
                    <span className="truncate">Attached: {uploadedDocName}</span>
                    <button
                      onClick={() => {
                        setDocumentId(null);
                        setUploadedDocName(null);
                      }}
                      className="ml-2 text-slate-400 hover:text-white"
                    >
                      ×
                    </button>
                  </div>
                )}

                {/* Upload error */}
                {uploadError && (
                  <div className="mb-2 rounded-lg border border-rose-400/30 bg-rose-400/10 px-3 py-1.5 text-xs text-rose-300">
                    {uploadError}
                  </div>
                )}

                {/* Controls bar */}
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-white/10 px-2 pt-3">
                  <div className="flex items-center gap-3">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".txt,.pdf,.docx"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploading || loading}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-300 transition hover:bg-white/10 disabled:opacity-40"
                    >
                      <span>📎</span>
                      <span>{uploading ? "Parsing doc…" : "Upload .txt / .pdf / .docx"}</span>
                    </button>
                    <span className="text-[11px] text-slate-500 font-mono">
                      {idea.length} chars
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={runResearch}
                    disabled={loading || idea.trim().length < 20}
                    className="rounded-xl bg-white px-5 py-2 text-xs font-semibold text-black transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-40 shadow-md"
                  >
                    {loading ? "RESEARCHING…" : "RUN RESEARCH →"}
                  </button>
                </div>
              </div>

              {/* Live progress indicator */}
              {loading && (
                <div className="mt-3 rounded-xl border border-cyan-400/20 bg-cyan-950/30 p-3 text-xs">
                  <div className="flex justify-between text-cyan-300 font-mono font-medium">
                    <span>{progressMsg || "RUNNING PIPELINE…"}</span>
                    <span>{progressPct}%</span>
                  </div>
                  <div className="mt-2 h-1.5 w-full rounded-full bg-white/10 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-400 to-blue-500 transition-all duration-300"
                      style={{ width: `${progressPct}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Status / feedback */}
              {statusFeedback && !loading && (
                <p className="mt-2 text-xs text-slate-400" aria-live="polite">
                  {statusFeedback}
                </p>
              )}
            </div>

            {/* Badges */}
            <div className="mt-7 flex flex-wrap gap-x-6 gap-y-2 text-[11px] uppercase tracking-[.2em] text-slate-500 font-medium">
              <span>TRACEABLE EVIDENCE</span>
              <span>ASYNC RUNS</span>
              <span>SCOPE-AWARE</span>
              <span>NO NOVELTY GUARANTEES</span>
            </div>
          </div>

          {/* 3D Scene */}
          <div className="relative">
            <LensScene />
          </div>
        </div>

        {/* Workflow Summary */}
        <div id="how" className="mt-12 grid gap-6 border-t border-white/10 py-10 md:grid-cols-4">
          <Mini n="01" t="DECOMPOSE" d="Problem · objective · methods · architecture · claims" />
          <Mini n="02" t="RETRIEVE" d="arXiv · Semantic Scholar · Crossref · GitHub" />
          <Mini n="03" t="ANALYZE" d="Similarity · contradictions · gaps · collisions" />
          <Mini n="04" t="DEFEND" d="Stress test · differentiation · traceable report" />
        </div>
      </section>

      {/* Analytical Pillars */}
      <section className="mx-auto max-w-7xl px-6 pb-12 md:px-10">
        <div className="grid gap-4 lg:grid-cols-3">
          <Signal n="07" t="ANALYSIS DIMENSIONS" d="Problem, objective, technology, method, architecture, dataset, domain." />
          <Signal n="04" t="SOURCE FAMILIES" d="Academic papers, Crossref, arXiv and GitHub repositories with deduplication." />
          <Signal n="01" t="EVIDENCE CHAIN" d="Conclusion → claim → excerpt → canonical source URL & identifier." />
        </div>
      </section>

      {/* Research Workspace & Dashboard */}
      <ResearchDashboard bundle={bundle} isLive={isLive} />

      {/* Footer */}
      <footer className="border-t border-white/10 px-6 py-8 text-xs text-slate-600 md:px-10">
        <div className="mx-auto flex max-w-7xl flex-wrap justify-between gap-4">
          <span>IDEALENS / TECHNICAL IDEA INTELLIGENCE ENGINE</span>
          <span>Similarity ≠ plagiarism · limited evidence ≠ novelty proof</span>
        </div>
      </footer>
    </main>
  );
}

function Mini({ n, t, d }: { n: string; t: string; d: string }) {
  return (
    <div>
      <div className="text-[10px] font-mono tracking-[.25em] text-cyan-300">{n}</div>
      <div className="mt-2 text-sm font-medium text-slate-200">{t}</div>
      <div className="mt-1 text-xs leading-5 text-slate-500">{d}</div>
    </div>
  );
}

function Signal({ n, t, d }: { n: string; t: string; d: string }) {
  return (
    <div className="glass rounded-2xl p-5 border border-white/5">
      <div className="text-3xl font-semibold text-slate-200">{n}</div>
      <div className="mt-3 text-xs tracking-[.2em] text-slate-500 font-semibold">{t}</div>
      <p className="mt-2 text-sm leading-6 text-slate-400">{d}</p>
    </div>
  );
}
