"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import LensScene from "../components/LensScene";
import ResearchDashboard from "../components/ResearchDashboard";
import {
  createResearchRun,
  pollResearchRun,
  fetchAllRunArtifacts,
  uploadDocument,
  listResearchRuns,
  getResearchRun,
  type ResearchRunResult,
  type ResearchRunSummaryItem,
  type RunArtifactsBundle,
} from "../lib/api/client";

export default function Home() {
  // Input and File State (Strictly decoupled)
  const [idea, setIdea] = useState("");
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [uploadedDocName, setUploadedDocName] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<{ title: string; message: string } | null>(null);

  // Research Pipeline Execution State
  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState<string | null>(null);
  const [progressPct, setProgressPct] = useState(0);

  // Active Research Bundle & Live Flag
  const [bundle, setBundle] = useState<RunArtifactsBundle | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [statusFeedback, setStatusFeedback] = useState<string | null>(null);

  // Workspace Tab Sync between 3D Scene and Dashboard
  const [activeWorkspaceTab, setActiveWorkspaceTab] = useState<string>("Overview");

  // Research History State
  const [history, setHistory] = useState<ResearchRunSummaryItem[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const runs = await listResearchRuns(30);
      setHistory(runs);
    } catch (err) {
      console.warn("Error fetching research history:", err);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    async function fetchInitialHistory() {
      try {
        const runs = await listResearchRuns(30);
        if (active) setHistory(runs);
      } catch (err) {
        console.warn("Error fetching research history:", err);
      }
    }
    fetchInitialHistory();
    return () => {
      active = false;
    };
  }, []);

  // Clean error-clearing handlers for input changes
  function handleIdeaChange(val: string) {
    setIdea(val);
    // CRITICAL: Typing a new idea immediately clears stale upload errors
    if (uploadError) {
      setUploadError(null);
    }
  }

  function handleRemoveFile() {
    setDocumentId(null);
    setUploadedDocName(null);
    setUploadError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

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
      setStatusFeedback(`Parsed ${doc.filename}: extracted text loaded into idea input.`);
    } catch (err: unknown) {
      const customCode = (err as unknown as { code?: string })?.code;
      const rawMsg = err instanceof Error ? err.message : "Document upload failed";

      let friendlyTitle = "DOCUMENT COULD NOT BE READ";
      let friendlyMessage = rawMsg;

      if (customCode === "PDF_TEXT_NOT_FOUND" || rawMsg.includes("scanned images")) {
        friendlyTitle = "SCANNED / IMAGE-ONLY PDF DETECTED";
        friendlyMessage =
          "This PDF appears to contain scanned images rather than selectable text. Please upload a text-based document or paste your text directly into the idea box.";
      } else if (customCode === "MALFORMED_PDF" || rawMsg.includes("corrupted")) {
        friendlyTitle = "CORRUPTED OR INVALID PDF";
        friendlyMessage = "The PDF structure could not be parsed. The file may be damaged or incomplete.";
      } else if (customCode === "EMPTY_FILE") {
        friendlyTitle = "EMPTY FILE";
        friendlyMessage = "The selected file is empty (0 bytes).";
      } else if (customCode === "FILE_TOO_LARGE") {
        friendlyTitle = "FILE EXCEEDS SIZE LIMIT";
        friendlyMessage = "The document exceeds the 10 MB maximum allowed limit.";
      }

      setUploadError({
        title: friendlyTitle,
        message: friendlyMessage,
      });
      // Do not overwrite user's typed idea on upload error
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function runResearch() {
    if (idea.trim().length < 20) return;
    setLoading(true);
    setUploadError(null);
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

      // Refresh history list
      loadHistory();
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

  async function handleSelectHistoryRun(runSummary: ResearchRunSummaryItem) {
    setLoading(true);
    setHistoryOpen(false);
    setStatusFeedback(`Loading research run: ${runSummary.title || runSummary.idea.slice(0, 50)}…`);
    try {
      const fullRun = await getResearchRun(runSummary.id);
      const loadedBundle = await fetchAllRunArtifacts(fullRun);
      setBundle(loadedBundle);
      setIdea(runSummary.idea);
      setIsLive(true);
      setStatusFeedback(`Restored historical research run from ${new Date(runSummary.created_at).toLocaleDateString()}.`);
      window.setTimeout(() => {
        document.getElementById("workspace")?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err) {
      console.error("Failed to restore history run:", err);
      setStatusFeedback("Could not restore selected research run.");
    } finally {
      setLoading(false);
    }
  }

  function handleStartNewIdea() {
    setIdea("");
    setDocumentId(null);
    setUploadedDocName(null);
    setUploadError(null);
    setHistoryOpen(false);
    document.getElementById("idea-box")?.focus();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <main className="grid-bg min-h-screen text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Navigation */}
      <nav className="fixed top-0 z-50 flex w-full items-center justify-between border-b border-white/5 bg-slate-950/80 px-6 py-4 backdrop-blur-md md:px-10">
        <div className="flex items-center gap-3">
          <div className="h-2.5 w-2.5 rounded-full bg-cyan-300 shadow-[0_0_18px_rgba(99,230,255,.9)]" />
          <span className="text-sm font-semibold tracking-[.25em] font-mono">IDEALENS</span>
        </div>

        <div className="hidden gap-7 text-xs font-medium tracking-wider text-slate-400 md:flex">
          <a href="#workspace" className="hover:text-cyan-300 transition">INTELLIGENCE</a>
          <a href="#how" className="hover:text-cyan-300 transition">METHOD</a>
          <a href="#workspace" className="hover:text-cyan-300 transition">TRACEABLE REPORT</a>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setHistoryOpen(true)}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3.5 py-1.5 text-xs font-medium text-slate-300 backdrop-blur transition hover:border-cyan-400/40 hover:bg-white/10"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
            <span>HISTORY ({history.length})</span>
          </button>

          <button
            onClick={handleStartNewIdea}
            className="rounded-full border border-cyan-400/40 bg-cyan-400/10 px-4 py-1.5 text-xs font-semibold text-cyan-200 backdrop-blur transition hover:bg-cyan-400/20 hover:text-white"
          >
            + NEW IDEA
          </button>
        </div>
      </nav>

      {/* History Slide-Out Drawer */}
      {historyOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative flex h-full w-full max-w-md flex-col border-l border-white/10 bg-slate-950 p-6 shadow-2xl animate-in slide-in-from-right duration-300 overflow-hidden">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div>
                <h3 className="text-base font-semibold text-white font-mono tracking-wider">
                  RESEARCH HISTORY
                </h3>
                <p className="text-xs text-slate-400">
                  Previous ideas persisted in the database
                </p>
              </div>
              <button
                onClick={() => setHistoryOpen(false)}
                className="rounded-lg border border-white/10 p-1.5 text-slate-400 hover:bg-white/5 hover:text-white"
                aria-label="Close history drawer"
              >
                ✕
              </button>
            </div>

            {/* History Run List */}
            <div className="mt-4 flex-1 overflow-y-auto space-y-3 pr-1">
              {loadingHistory ? (
                <div className="py-12 text-center text-xs text-slate-500 font-mono">
                  LOADING PREVIOUS RUNS…
                </div>
              ) : history.length === 0 ? (
                <div className="py-16 text-center text-xs text-slate-500">
                  No previous research runs recorded yet. Submit your first technical idea to generate intelligence.
                </div>
              ) : (
                history.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => handleSelectHistoryRun(item)}
                    className="cursor-pointer rounded-2xl border border-white/10 bg-white/5 p-4 transition hover:border-cyan-400/40 hover:bg-white/10 shadow-sm"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className={`rounded-full px-2 py-0.5 text-[9px] font-mono uppercase font-bold ${
                        item.status === "completed"
                          ? "bg-emerald-400/10 text-emerald-300 border border-emerald-400/30"
                          : "bg-cyan-400/10 text-cyan-300 border border-cyan-400/30"
                      }`}>
                        {item.status}
                      </span>
                      <span className="text-[11px] font-mono text-slate-500">
                        {new Date(item.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                      </span>
                    </div>

                    <h4 className="mt-2 text-sm font-semibold text-slate-200 line-clamp-2">
                      {item.title || item.idea}
                    </h4>

                    <p className="mt-1 text-xs text-slate-400 line-clamp-2">
                      {item.idea}
                    </p>

                    <div className="mt-3 flex items-center justify-between border-t border-white/10 pt-2 text-[11px] text-slate-400 font-mono">
                      <span>{item.sources_count} sources · {item.evidence_count} evidence</span>
                      <span className="text-cyan-300 font-bold">Signal: {item.decision_signal}</span>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="border-t border-white/10 pt-4">
              <button
                onClick={handleStartNewIdea}
                className="w-full rounded-xl bg-white/10 py-2.5 text-xs font-semibold text-white transition hover:bg-white/15"
              >
                + Analyze a New Idea
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <section className="relative mx-auto flex min-h-screen max-w-7xl flex-col justify-center px-6 pt-24 md:px-10">
        <div className="grid items-center gap-8 lg:grid-cols-[1fr_1.1fr]">
          <div className="relative z-10">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/5 px-3 py-1 text-[10px] font-semibold tracking-[.3em] text-cyan-300 font-mono">
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
                  onChange={(e) => handleIdeaChange(e.target.value)}
                  placeholder="Describe your technical idea, hypothesis, or paste research proposal..."
                  className="h-32 w-full resize-none bg-transparent p-3 text-sm text-white outline-none placeholder:text-slate-600"
                />

                {/* Uploaded doc badge */}
                {uploadedDocName && (
                  <div className="mb-2 flex items-center justify-between rounded-lg border border-cyan-400/30 bg-cyan-400/10 px-3 py-1.5 text-xs text-cyan-200">
                    <span className="truncate">Attached: {uploadedDocName}</span>
                    <button
                      onClick={handleRemoveFile}
                      aria-label="Remove attached document"
                      className="ml-2 text-slate-400 hover:text-white"
                    >
                      ×
                    </button>
                  </div>
                )}

                {/* Friendly Upload Error Card with immediate reset */}
                {uploadError && (
                  <div className="mb-3 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-200 shadow-md">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="font-bold tracking-wider text-rose-300 font-mono text-[10px]">
                          {uploadError.title}
                        </div>
                        <p className="mt-1 leading-5 text-rose-100">
                          {uploadError.message}
                        </p>
                      </div>
                      <button
                        onClick={() => setUploadError(null)}
                        className="text-rose-400 hover:text-white font-bold p-1"
                        aria-label="Dismiss error"
                      >
                        ✕
                      </button>
                    </div>
                    <div className="mt-2.5 flex items-center gap-3 border-t border-rose-500/20 pt-2">
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="font-semibold underline text-rose-300 hover:text-white"
                      >
                        Try another file
                      </button>
                      <span className="text-rose-400/60">·</span>
                      <span className="text-[11px] text-rose-300/80">
                        Or continue typing your idea above
                      </span>
                    </div>
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
                      onClick={() => {
                        setUploadError(null);
                        fileInputRef.current?.click();
                      }}
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
                <p className="mt-2 text-xs text-slate-400 font-mono" aria-live="polite">
                  {statusFeedback}
                </p>
              )}
            </div>

            {/* Badges */}
            <div className="mt-7 flex flex-wrap gap-x-6 gap-y-2 text-[11px] uppercase tracking-[.2em] text-slate-500 font-medium font-mono">
              <span>TRACEABLE EVIDENCE</span>
              <span>ASYNC RUNS</span>
              <span>SCOPE-AWARE</span>
              <span>NO NOVELTY GUARANTEES</span>
            </div>
          </div>

          {/* 3D Scene with Tab Sync */}
          <div className="relative">
            <LensScene
              bundle={bundle}
              onSelectTab={(tabName) => setActiveWorkspaceTab(tabName)}
            />
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

      {/* Research Workspace & Dashboard with Tab Sync */}
      <ResearchDashboard
        bundle={bundle}
        isLive={isLive}
        activeTab={activeWorkspaceTab}
        onTabChange={setActiveWorkspaceTab}
      />

      {/* Footer */}
      <footer className="border-t border-white/10 px-6 py-8 text-xs text-slate-600 md:px-10">
        <div className="mx-auto flex max-w-7xl flex-wrap justify-between gap-4 font-mono">
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
      <div className="text-3xl font-semibold text-slate-200 font-mono">{n}</div>
      <div className="mt-3 text-xs tracking-[.2em] text-slate-500 font-semibold font-mono">{t}</div>
      <p className="mt-2 text-sm leading-6 text-slate-400">{d}</p>
    </div>
  );
}
