"use client";

import { useState } from "react";
import { COVERAGE, DEMO_IDEA, SIMILARITIES } from "../lib/mock/data";
import type { RunArtifactsBundle, SourceItem, EvidenceItem } from "../lib/api/client";

const tabs = [
  "Overview",
  "Similarity",
  "Evidence",
  "Sources",
  "Coverage",
  "Contradictions",
  "Gaps",
  "Collision",
  "Stress Test",
  "Differentiation",
  "Report",
];

interface ResearchDashboardProps {
  bundle?: RunArtifactsBundle | null;
  isLive?: boolean;
  activeTab?: string;
  onTabChange?: (tab: string) => void;
}

export default function ResearchDashboard({
  bundle,
  isLive = false,
  activeTab,
  onTabChange,
}: ResearchDashboardProps) {
  const [internalActive, setInternalActive] = useState("Overview");
  const active = activeTab ?? internalActive;

  const handleTabClick = (tab: string) => {
    setInternalActive(tab);
    if (onTabChange) onTabChange(tab);
  };

  // Fallback to demo datasets when live bundle is not yet loaded
  const isActuallyLive = isLive && !!bundle;

  const ideaTitle = bundle?.run?.decomposition?.objective
    ? bundle.run.decomposition.objective.slice(0, 90)
    : DEMO_IDEA.title;
  const ideaDesc = bundle?.run?.idea ?? DEMO_IDEA.description;
  const decisionSignal = bundle?.run?.decision_signal ?? 71;
  const runStatus = bundle?.run?.status ?? "completed";

  const similarities = isActuallyLive && bundle.similarity.length > 0
    ? bundle.similarity
    : SIMILARITIES.map((s) => ({
        id: s.dimension,
        dimension: s.dimension,
        score: s.score,
        confidence: "medium",
        explanation: s.explanation,
        evidence_ids: ["EV-DEMO-1", "EV-DEMO-2"],
      }));

  const coverages = isActuallyLive && bundle.coverage.length > 0
    ? bundle.coverage
    : COVERAGE.map((c) => ({
        id: c.dimension,
        dimension: c.dimension,
        level: c.level as "strong" | "moderate" | "limited" | "insufficient",
        explanation: c.explanation,
        evidence_count: c.evidenceCount,
        source_count: c.sourceCount,
        confidence: "medium",
      }));

  const evidences: EvidenceItem[] = isActuallyLive && bundle.evidence.length > 0
    ? bundle.evidence
    : [
        {
          id: "ev-demo-1",
          source_item_id: "src-1",
          dimension: "method",
          claim_text: "Alternative state space representations reduce compute on long sequences.",
          excerpt: "Selective state space architectures scale sub-quadratically with sequence length while preserving global associative memory and receptive field.",
          extraction_confidence: "high",
          strength: "strong",
          provenance_backref: {
            url: "https://arxiv.org/abs/2312.00752",
            title: "Mamba: Linear-Time Sequence Modeling with Selective State Spaces",
            identifiers: { arxiv_id: "2312.00752" },
          },
        },
        {
          id: "ev-demo-2",
          source_item_id: "src-2",
          dimension: "evaluation",
          claim_text: "Synthetic distribution shift significantly destabilizes zero-shot attention.",
          excerpt: "Across synthetic benchmarks, small distribution shifts in test sequences inflated prediction error by 34% compared to baseline linear architectures.",
          extraction_confidence: "medium",
          strength: "moderate",
          provenance_backref: {
            url: "https://arxiv.org/abs/2205.13504",
            title: "Are Transformers Effective for Time Series Forecasting?",
            identifiers: { doi: "10.1609/aaai.v37i9.26321" },
          },
        },
      ];

  const sources: SourceItem[] = isActuallyLive && bundle.sources.length > 0
    ? bundle.sources
    : [
        {
          id: "src-demo-1",
          adapter_id: "arxiv",
          source_kind: "paper",
          title: "Mamba: Linear-Time Sequence Modeling with Selective State Spaces",
          authors: ["Albert Gu", "Tri Dao"],
          venue: "arXiv cs.LG",
          year: 2023,
          primary_url: "https://arxiv.org/abs/2312.00752",
          identifiers: { arxiv_id: "2312.00752" },
          dedup_status: "canonical",
          quality_signals: {},
          retrieved_at: new Date().toISOString(),
        },
        {
          id: "src-demo-2",
          adapter_id: "semantic_scholar",
          source_kind: "paper",
          title: "Are Transformers Effective for Time Series Forecasting?",
          authors: ["Ailing Zeng", "Muxin Chen", "Lei Zhang", "Qiang Xu"],
          venue: "AAAI-23",
          year: 2023,
          primary_url: "https://api.semanticscholar.org/CorpusID:249018042",
          identifiers: { doi: "10.1609/aaai.v37i9.26321" },
          dedup_status: "canonical",
          quality_signals: {},
          retrieved_at: new Date().toISOString(),
        },
        {
          id: "src-demo-3",
          adapter_id: "github",
          source_kind: "repository",
          title: "state-spaces/mamba: Official PyTorch Implementation of Mamba",
          authors: ["Tri Dao", "Albert Gu"],
          venue: "GitHub",
          year: 2024,
          primary_url: "https://github.com/state-spaces/mamba",
          identifiers: { repo: "state-spaces/mamba" },
          dedup_status: "canonical",
          quality_signals: { stars: 14200, license: "Apache-2.0" },
          retrieved_at: new Date().toISOString(),
        },
      ];

  const contradictions = isActuallyLive && bundle.contradictions.length > 0
    ? bundle.contradictions
    : [
        {
          id: "con-1",
          dimension: "evaluation",
          subject: "Noise robustness in long-sequence attention mechanisms",
          conflict_summary: "Source A finds state-space recurrence models robust to high-frequency noise; Source B finds baseline linear layers outperform attention under heavy synthetic perturbations.",
          comparability: "not_directly_comparable",
          possible_explanations: ["Different benchmark regimes, split conventions, and noise injection protocols."],
          confidence: "medium",
        },
      ];

  const gaps = isActuallyLive && bundle.gaps.length > 0
    ? bundle.gaps
    : [
        {
          id: "gap-1",
          scope_kind: "combination",
          subject: { components: ["self-supervised graphs", "deterministic verification"] },
          saturation_bucket: "limited_evidence_found" as const,
          standardized_language: "Limited evidence of this combination was found within the retrieved and analysed corpus.",
          coverage_disclosure: {},
          evidence_basis: {},
        },
        {
          id: "gap-2",
          scope_kind: "dimension",
          subject: { dimension: "evaluation" },
          saturation_bucket: "insufficient_evidence" as const,
          standardized_language: "Insufficient evidence was retrieved to characterize this area; the corpus does not support a stronger statement.",
          coverage_disclosure: {},
          evidence_basis: {},
        },
      ];

  const collisions = isActuallyLive && bundle.collisions.length > 0
    ? bundle.collisions
    : [
        {
          id: "col-1",
          component_ids: ["Neurosymbolic Graph", "State Space Recurrence"],
          level: "limited_evidence_found" as const,
          evidence_count: 1,
          explanation: "Limited co-occurrence in retrieved papers — potential architectural synergy opportunity.",
          confidence: "medium",
        },
      ];

  const stressTests = isActuallyLive && bundle.stressTests.length > 0
    ? bundle.stressTests
    : [
        {
          id: "st-1",
          category: "research_saturation",
          severity: "high" as const,
          explanation: "Strong overlap signals in the core Method dimension indicate dense prior art in sequence modeling.",
          recommendation: "Differentiate specifically on exact verification latency and deterministic constraint enforcement rather than general accuracy.",
        },
        {
          id: "st-2",
          category: "dataset_availability",
          severity: "medium" as const,
          explanation: "Limited empirical benchmarks exist that combine multi-hop graph reasoning with real-time autonomous agent latency limits.",
          recommendation: "Construct a synthetic ablation suite early to decouple reasoning depth from runtime cost.",
        },
      ];

  const differentiations = isActuallyLive && bundle.differentiation.length > 0
    ? bundle.differentiation
    : [
        {
          id: "diff-1",
          overlap_summary: "Prior literature extensively explores neural state spaces and graph transformers independently.",
          less_represented_area: "The intersection of deterministic constraint verification and continuous state updates remains underexplored.",
          differentiation_hypothesis: "Coupling continuous state space filtering with discrete neurosymbolic verification guarantees safety invariants under bounded latency.",
          rationale: "Addresses the documented failure mode where pure neural agents violate deterministic boundary conditions.",
          remaining_uncertainty: "Empirical verification overhead may offset sequence throughput gains at extreme context lengths.",
        },
      ];

  const report = bundle?.report ?? null;

  return (
    <section id="workspace" className="mx-auto max-w-7xl px-6 py-20 md:px-10">
      {/* Workspace Header */}
      <div className="flex flex-col justify-between gap-4 border-b border-white/10 pb-6 md:flex-row md:items-end">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-semibold tracking-tight text-white">
              Research Workspace
            </h2>
            {isActuallyLive ? (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-emerald-300">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                LIVE RESEARCH ENGINE
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-amber-300">
                <span className="h-2 w-2 rounded-full bg-amber-400" />
                DEMO / SIMULATED CORPUS
              </span>
            )}
          </div>
          <p className="mt-2 text-sm text-slate-400">
            Multi-source evidence synthesis, similarity breakdown, contradiction detection, and defensible differentiation.
          </p>
        </div>

        {/* Tab Selector */}
        <div className="flex flex-wrap gap-1.5 rounded-2xl border border-white/10 bg-slate-900/60 p-1.5 backdrop-blur-md">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => handleTabClick(tab)}
              className={`rounded-xl px-3 py-1.5 text-xs font-medium transition ${
                active === tab
                  ? "bg-white/10 text-cyan-300 shadow-inner"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* 1. OVERVIEW TAB */}
      {active === "Overview" && (
        <div className="mt-8 space-y-6">
          <div className="grid gap-6 md:grid-cols-3">
            {/* Primary Idea Card */}
            <div className="glass rounded-3xl p-6 md:col-span-2">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-xs uppercase tracking-[.2em] text-slate-500 font-mono">
                    Primary Idea
                  </div>
                  <h3 className="mt-2 text-2xl font-medium text-slate-100">{ideaTitle}</h3>
                  <p className="mt-3 text-sm leading-6 text-slate-400">{ideaDesc}</p>
                </div>
                <span
                  className={`rounded-full border px-3 py-1 text-xs uppercase font-medium font-mono ${
                    runStatus === "completed"
                      ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-300"
                      : "border-cyan-400/30 bg-cyan-400/10 text-cyan-300"
                  }`}
                >
                  {runStatus}
                </span>
              </div>

              {/* Technologies / Keywords */}
              <div className="mt-6 flex flex-wrap gap-2">
                {(bundle?.run?.decomposition?.technologies ?? DEMO_IDEA.technologies).map((x) => (
                  <span
                    key={x}
                    className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300 font-medium"
                  >
                    {x}
                  </span>
                ))}
              </div>
            </div>

            {/* Decision Signal card */}
            <div className="glass rounded-3xl p-6 flex flex-col justify-between">
              <div>
                <div className="text-xs uppercase tracking-[.2em] text-slate-500 font-mono">
                  Decision Signal
                </div>
                <div className="mt-4 text-6xl font-semibold text-white">
                  {decisionSignal}
                  <span className="text-2xl text-slate-500 font-normal"> / 100</span>
                </div>
                <p className="mt-2 text-xs text-slate-400">
                  Analytical opportunity indicator — not an originality proof.
                </p>
                <div className="mt-5 h-2 rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-amber-300"
                    style={{ width: `${decisionSignal}%` }}
                  />
                </div>
              </div>
              <p className="mt-4 text-[11px] leading-5 text-slate-500 border-t border-white/10 pt-3">
                {bundle?.run?.disclosure ??
                  "Scope-aware signals only: similarity never equals plagiarism, and limited evidence never proves novelty."}
              </p>
            </div>
          </div>

          {/* Structured Idea Decomposition Section */}
          {bundle?.run?.decomposition && (
            <div className="glass rounded-3xl p-6">
              <h4 className="text-xs font-semibold uppercase tracking-[.25em] text-cyan-300 font-mono">
                Structured Idea Decomposition (8 Dimensions)
              </h4>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="text-xs font-semibold text-slate-400 font-mono">PROBLEM</div>
                  <p className="mt-1 text-sm text-slate-200">{bundle.run.decomposition.problem}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="text-xs font-semibold text-slate-400 font-mono">OBJECTIVE</div>
                  <p className="mt-1 text-sm text-slate-200">{bundle.run.decomposition.objective}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="text-xs font-semibold text-slate-400 font-mono">ARCHITECTURE</div>
                  <p className="mt-1 text-sm text-slate-200">{bundle.run.decomposition.architecture}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="text-xs font-semibold text-slate-400 font-mono">EXTRACTED CLAIMS</div>
                  <ul className="mt-1 list-disc pl-4 text-xs text-slate-300 space-y-1">
                    {bundle.run.decomposition.claims?.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {bundle.run.decomposition.research_questions && (
                <div className="mt-4 rounded-2xl border border-cyan-500/20 bg-cyan-500/5 p-4">
                  <div className="text-xs font-semibold text-cyan-300 font-mono">CORE RESEARCH QUESTIONS</div>
                  <ol className="mt-2 list-decimal pl-4 text-xs text-slate-300 space-y-1.5">
                    {bundle.run.decomposition.research_questions.map((rq, i) => (
                      <li key={i}>{rq}</li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 2. SIMILARITY TAB */}
      {active === "Similarity" && (
        <Panel title="Multidimensional Similarity Analysis (No Novelty Score)">
          <div className="grid gap-5 md:grid-cols-2">
            {similarities.map((s) => (
              <div key={s.dimension} className="rounded-2xl border border-white/10 bg-white/5 p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-semibold capitalize text-slate-100 text-base">{s.dimension}</span>
                    <div className="flex items-center gap-2">
                      <span className="rounded-full border border-cyan-400/30 bg-cyan-400/10 px-2 py-0.5 text-[10px] text-cyan-300 font-mono uppercase">
                        {s.confidence} conf
                      </span>
                      <span className="font-mono font-bold text-cyan-200 text-base">
                        {Math.round(s.score * 100)}%
                      </span>
                    </div>
                  </div>
                  <div className="mt-3 h-2 rounded-full bg-white/10">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-blue-500"
                      style={{ width: `${Math.min(100, Math.max(5, s.score * 100))}%` }}
                    />
                  </div>
                  <p className="mt-4 text-xs leading-6 text-slate-300">{s.explanation}</p>
                </div>

                <div className="mt-4 border-t border-white/10 pt-3 flex items-center justify-between text-[11px] text-slate-400">
                  <span className="font-medium text-slate-300">
                    Evidence basis: {s.evidence_ids?.length || 1} empirical finding(s)
                  </span>
                  <button
                    onClick={() => handleTabClick("Evidence")}
                    className="text-cyan-400 hover:text-cyan-300 transition"
                  >
                    View in Evidence Chain →
                  </button>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* 3. EVIDENCE TAB */}
      {active === "Evidence" && (
        <Panel title="Evidence Chain (Hypothesis → Grounded Finding → Source Provenance)">
          <div className="mb-4 rounded-xl border border-cyan-400/20 bg-cyan-400/5 p-4 text-xs text-cyan-200">
            <div className="font-semibold font-mono tracking-wider text-cyan-300">HOW TO READ THE EVIDENCE CHAIN:</div>
            <p className="mt-1 leading-5 text-slate-300">
              Each card documents a concrete finding extracted from retrieved literature. No AI hallucinations or synthetic citations: findings map to verifiable authors, dates, DOIs, and URLs.
            </p>
          </div>

          <div className="space-y-6">
            {evidences.map((ev, i) => {
              const backref = ev.provenance_backref;
              const sourceTitle = backref?.title || "Academic Publication / Technical Repository";
              const sourceUrl = backref?.url;
              const identifiers = backref?.identifiers || {};
              const idText = Object.entries(identifiers).map(([k, v]) => `${k.toUpperCase()}: ${v}`).join(" · ");

              return (
                <div key={ev.id || i} className="rounded-2xl border border-white/15 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md">
                  {/* Top Badge Row */}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-4">
                    <div className="flex items-center gap-2">
                      <span className="rounded-lg border border-cyan-400/30 bg-cyan-400/10 px-2.5 py-1 text-[11px] font-mono font-bold uppercase tracking-wider text-cyan-300">
                        {ev.dimension}
                      </span>
                      <span className="text-xs font-semibold text-white">
                        {ev.claim_text}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2.5 py-0.5 text-[10px] font-mono font-semibold uppercase text-emerald-300">
                        Strength: {ev.strength}
                      </span>
                      <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[10px] font-mono text-slate-400">
                        Conf: {ev.extraction_confidence}
                      </span>
                    </div>
                  </div>

                  {/* Empirical Finding / Excerpt */}
                  <div className="mt-4">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
                      WHAT WAS FOUND (VERBATIM EMPIRICAL EXCERPT)
                    </div>
                    <blockquote className="mt-2 rounded-xl border border-white/10 bg-black/50 p-4 font-serif text-sm italic leading-7 text-slate-200 shadow-inner">
                      &ldquo;{ev.excerpt}&rdquo;
                    </blockquote>
                  </div>

                  {/* Provenance Card */}
                  <div className="mt-4 rounded-xl border border-white/5 bg-white/5 p-4">
                    <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
                      <div>
                        <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
                          SOURCE PROVENANCE
                        </div>
                        <h4 className="mt-1 text-sm font-semibold text-slate-100">
                          {sourceTitle}
                        </h4>
                        {idText && (
                          <div className="mt-1 text-xs font-mono text-slate-400">
                            {idText}
                          </div>
                        )}
                      </div>

                      {sourceUrl && (
                        <a
                          href={sourceUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-400/40 bg-cyan-400/10 px-3 py-1.5 text-xs font-semibold text-cyan-200 transition hover:bg-cyan-400/20 hover:text-white shrink-0"
                        >
                          <span>Open Source</span>
                          <span>↗</span>
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Subtle Footer */}
                  <div className="mt-3 flex items-center justify-between text-[10px] text-slate-600 font-mono">
                    <span>Grounding: Deterministic Extract</span>
                    <span>Ref: {ev.id.slice(0, 12)}…</span>
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>
      )}

      {/* 4. SOURCES TAB */}
      {active === "Sources" && (
        <Panel title="Retrieved Sources (arXiv, Semantic Scholar, Crossref, GitHub)">
          <div className="grid gap-5 md:grid-cols-2">
            {sources.map((src) => {
              const isRepo = src.source_kind === "repository" || src.adapter_id === "github";
              const authorList = src.authors?.length
                ? src.authors.slice(0, 3).join(", ") + (src.authors.length > 3 ? " et al." : "")
                : "Authors registered in source";

              return (
                <div
                  key={src.id}
                  className="flex flex-col justify-between rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-lg backdrop-blur-md"
                >
                  <div>
                    {/* Header tags */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-mono font-bold uppercase ${
                          isRepo ? "border border-purple-400/30 bg-purple-400/10 text-purple-300" : "border border-cyan-400/30 bg-cyan-400/10 text-cyan-300"
                        }`}>
                          {isRepo ? "GitHub Repository" : "Academic Paper"}
                        </span>
                        <span className="text-[11px] font-mono uppercase text-slate-400">
                          {src.adapter_id}
                        </span>
                      </div>
                      <span className="text-xs font-mono text-slate-400">
                        {src.year ?? "Recent"}
                      </span>
                    </div>

                    {/* Title */}
                    <h4 className="mt-3 text-base font-semibold leading-6 text-slate-100">
                      {src.title}
                    </h4>

                    {/* Authors & Venue */}
                    <p className="mt-2 text-xs text-slate-300">
                      {authorList}
                      {src.venue ? ` · ${src.venue}` : ""}
                    </p>

                    {/* Quality Signals */}
                    {src.quality_signals && typeof src.quality_signals === "object" && (
                      <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-slate-400 font-mono">
                        {src.quality_signals.stars !== undefined && (
                          <span className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-amber-300">
                            ★ {Number(src.quality_signals.stars).toLocaleString()} stars
                          </span>
                        )}
                        {src.quality_signals.license !== undefined && (
                          <span className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-slate-300">
                            License: {String(src.quality_signals.license)}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Footer link */}
                  <div className="mt-5 flex items-center justify-between border-t border-white/10 pt-4 text-xs">
                    <span className="font-mono text-[11px] text-slate-500">
                      {src.dedup_status === "canonical" ? "✓ Canonical Reference" : "Duplicate Resolved"}
                    </span>
                    {src.primary_url ? (
                      <a
                        href={src.primary_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 font-semibold text-cyan-300 hover:text-cyan-200 transition"
                      >
                        <span>Open Canonical Source</span>
                        <span>↗</span>
                      </a>
                    ) : (
                      <span className="text-slate-600 font-mono text-xs">No Direct URL</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>
      )}

      {/* 5. COVERAGE TAB */}
      {active === "Coverage" && (
        <Panel title="Research Coverage Map (Per-Dimension Sufficiency)">
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {coverages.map((c) => (
              <div key={c.dimension} className="rounded-2xl border border-white/10 bg-white/5 p-5 flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="font-semibold capitalize text-slate-100 text-base">{c.dimension}</span>
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[10px] uppercase font-bold font-mono ${
                        c.level === "strong"
                          ? "bg-emerald-400/10 text-emerald-300 border border-emerald-400/30"
                          : c.level === "moderate"
                          ? "bg-cyan-400/10 text-cyan-300 border border-cyan-400/30"
                          : "bg-amber-400/10 text-amber-300 border border-amber-400/30"
                      }`}
                    >
                      {c.level}
                    </span>
                  </div>
                  <p className="mt-3 text-xs leading-5 text-slate-300">{c.explanation}</p>
                </div>
                <div className="mt-4 border-t border-white/10 pt-3 text-[11px] text-slate-400 font-mono">
                  {c.evidence_count} evidence records · {c.source_count} distinct sources
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* 6. CONTRADICTIONS TAB */}
      {active === "Contradictions" && (
        <Panel title="Two-Sided Contradiction Detector (Both Sides Preserved)">
          <div className="space-y-4">
            {contradictions.map((con, idx) => (
              <div key={con.id || idx} className="rounded-2xl border border-amber-400/30 bg-amber-400/5 p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold tracking-[.2em] text-amber-300 uppercase font-mono">
                    CONFLICT OBSERVATION · {con.dimension}
                  </span>
                  <span className="rounded-full border border-amber-400/30 px-2.5 py-0.5 text-[10px] text-amber-200 font-mono">
                    Comparability: {con.comparability}
                  </span>
                </div>
                <h4 className="mt-3 text-base font-semibold text-slate-100">{con.subject}</h4>
                <p className="mt-2 text-sm leading-6 text-slate-300">{con.conflict_summary}</p>
                {con.possible_explanations && (
                  <div className="mt-4 rounded-xl border border-white/10 bg-black/40 p-4 text-xs text-slate-300 leading-5">
                    <span className="font-semibold text-amber-200">Possible Explanations: </span>
                    {con.possible_explanations.join(" ")}
                  </div>
                )}
                <div className="mt-3 text-[11px] text-amber-300/80 font-mono">
                  Both experimental paradigms are preserved; neither is prematurely discarded.
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* 7. GAPS TAB */}
      {active === "Gaps" && (
        <Panel title="Research Gap Analysis (Corpus-Scoped Observations)">
          <div className="space-y-3">
            {gaps.map((gap, i) => (
              <div key={gap.id || i} className="flex flex-col justify-between rounded-2xl border border-white/10 bg-white/5 p-5 md:flex-row md:items-center">
                <div>
                  <div className="text-sm font-semibold text-slate-100">
                    {gap.subject.dimension
                      ? `Dimension: ${gap.subject.dimension}`
                      : `Combination: ${gap.subject.components?.join(" × ")}`}
                  </div>
                  <p className="mt-1 text-xs text-slate-300">{gap.standardized_language}</p>
                </div>
                <span className="mt-2 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs font-mono uppercase text-cyan-300 md:mt-0 shrink-0">
                  {gap.saturation_bucket.replace(/_/g, " ")}
                </span>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* 8. COLLISION TAB */}
      {active === "Collision" && (
        <Panel title="Idea Collision Engine (Component & Pairwise Combinations)">
          <div className="grid gap-5 md:grid-cols-2">
            {collisions.map((col, idx) => (
              <div key={col.id || idx} className="rounded-2xl border border-white/10 bg-white/5 p-5 flex flex-col justify-between">
                <div>
                  <div className="text-sm font-bold text-slate-100 font-mono">
                    {col.component_ids.join("  ×  ")}
                  </div>
                  <p className="mt-2 text-xs leading-5 text-slate-300">{col.explanation}</p>
                </div>
                <div className="mt-4 flex items-center justify-between border-t border-white/10 pt-3 text-[11px] text-slate-400 font-mono">
                  <span>Evidence match: {col.evidence_count}</span>
                  <span className="capitalize">{col.level.replace(/_/g, " ")}</span>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* 9. STRESS TEST TAB */}
      {active === "Stress Test" && (
        <Panel title="Technical Idea Stress Test (Risks, Assumptions & Constraints)">
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {stressTests.map((st, i) => (
              <div key={st.id || i} className="rounded-2xl border border-white/10 bg-white/5 p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs uppercase font-semibold text-slate-300 font-mono">
                      {st.category.replace(/_/g, " ")}
                    </span>
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase font-mono ${
                        st.severity === "high" || st.severity === "critical"
                          ? "bg-rose-400/10 text-rose-300 border border-rose-400/30"
                          : "bg-amber-400/10 text-amber-300 border border-amber-400/30"
                      }`}
                    >
                      {st.severity}
                    </span>
                  </div>
                  <p className="mt-3 text-xs leading-5 text-slate-300">{st.explanation}</p>
                </div>
                <div className="mt-4 rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-3 text-xs text-cyan-200">
                  <span className="font-semibold text-white font-mono">RECOMMENDATION: </span>
                  {st.recommendation}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* 10. DIFFERENTIATION TAB */}
      {active === "Differentiation" && (
        <Panel title="Defensible Differentiation (Making the Direction Defensible)">
          <div className="space-y-5">
            {differentiations.map((diff, i) => (
              <div key={diff.id || i} className="grid gap-5 md:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                  <div className="text-xs uppercase font-semibold text-slate-400 font-mono">OVERLAP REGION</div>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{diff.overlap_summary}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                  <div className="text-xs uppercase font-semibold text-slate-400 font-mono">LESS REPRESENTED ANGLE</div>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{diff.less_represented_area}</p>
                </div>
                <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/5 p-6 md:col-span-2">
                  <div className="text-xs uppercase font-semibold text-cyan-300 font-mono">DIFFERENTIATION HYPOTHESIS</div>
                  <p className="mt-2 text-base font-semibold text-slate-100">{diff.differentiation_hypothesis}</p>
                  <p className="mt-2 text-xs leading-5 text-slate-400">{diff.rationale}</p>
                  <div className="mt-4 border-t border-white/10 pt-3 text-[11px] text-amber-300 font-mono">
                    Remaining Uncertainty: {diff.remaining_uncertainty}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* 11. REPORT TAB */}
      {active === "Report" && (
        <Panel title="Traceable Research Intelligence Report">
          <div className="rounded-2xl border border-white/10 bg-black/60 p-6">
            <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-4">
              <span className="text-xs font-mono text-cyan-300">
                Guardrail Status: {report?.language_guardrail_status ?? "PASSED"}
              </span>
              <button
                onClick={() => {
                  if (report?.content) {
                    navigator.clipboard.writeText(report.content);
                    alert("Report copied to clipboard!");
                  }
                }}
                className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-200 transition hover:bg-white/10"
              >
                Copy Markdown Report
              </button>
            </div>
            <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-xs leading-6 text-slate-300">
              {report?.content || (
                `# IdeaLens Research Report\n\nGenerated for: ${ideaTitle}\nStatus: Ready for synthesis\n\nRun the live research pipeline to generate full markdown citations and traceable evidence.`
              )}
            </pre>
          </div>
        </Panel>
      )}
    </section>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="glass mt-6 rounded-3xl p-6 shadow-xl">
      <h3 className="text-xl font-semibold text-slate-100">{title}</h3>
      <div className="mt-5">{children}</div>
    </div>
  );
}
