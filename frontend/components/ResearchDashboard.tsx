"use client";

import { useState } from "react";
import { COVERAGE, DEMO_IDEA, SIMILARITIES } from "../lib/mock/data";
import type { RunArtifactsBundle } from "../lib/api/client";

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

export default function ResearchDashboard({
  bundle,
  isLive = false,
}: {
  bundle?: RunArtifactsBundle | null;
  isLive?: boolean;
}) {
  const [active, setActive] = useState("Overview");

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
        evidence_ids: ["EV-DEMO"],
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

  const evidences = isActuallyLive && bundle.evidence.length > 0
    ? bundle.evidence
    : [
        {
          id: "ev-1",
          source_item_id: "src-1",
          dimension: "method",
          claim_text: "Alternative attention routing may reduce compute on long horizons.",
          excerpt: "Sparse state space representations scale sub-quadratically while preserving receptive field.",
          extraction_confidence: "high",
          strength: "strong",
          provenance_backref: { url: "https://arxiv.org/abs/2312.00752", title: "Mamba: Linear-Time Sequence Modeling" },
        },
        {
          id: "ev-2",
          source_item_id: "src-2",
          dimension: "evaluation",
          claim_text: "Noise and distribution shift destabilize zero-shot forecasting.",
          excerpt: "Across synthetic benchmarks, small perturbations in test distribution led to 34% error inflation.",
          extraction_confidence: "medium",
          strength: "moderate",
          provenance_backref: { url: "https://arxiv.org/abs/2205.13504", title: "Are Transformers Effective for Time Series?" },
        },
      ];

  const sources = isActuallyLive && bundle.sources.length > 0
    ? bundle.sources
    : [
        {
          id: "src-1",
          adapter_id: "arxiv",
          source_kind: "paper",
          title: "Mamba: Linear-Time Sequence Modeling with Selective State Spaces",
          authors: ["Albert Gu", "Tri Dao"],
          venue: "arXiv",
          year: 2023,
          primary_url: "https://arxiv.org/abs/2312.00752",
          identifiers: { arxiv_id: "2312.00752" },
          dedup_status: "canonical",
          quality_signals: {},
          retrieved_at: new Date().toISOString(),
        },
        {
          id: "src-2",
          adapter_id: "semantic_scholar",
          source_kind: "paper",
          title: "Are Transformers Effective for Time Series Forecasting?",
          authors: ["Ailing Zeng", "Muxin Chen", "Lei Zhang", "Qiang Xu"],
          venue: "AAAI",
          year: 2023,
          primary_url: "https://api.semanticscholar.org/CorpusID:249018042",
          identifiers: { doi: "10.1609/aaai.v37i9.26321" },
          dedup_status: "canonical",
          quality_signals: {},
          retrieved_at: new Date().toISOString(),
        },
      ];

  const contradictions = isActuallyLive && bundle.contradictions.length > 0
    ? bundle.contradictions
    : [
        {
          id: "con-1",
          dimension: "evaluation",
          subject: "Noise robustness in time-series attention",
          conflict_summary: "Source A finds state space models robust to noise; Source B finds baseline linear layers outperform attention under heavy noise.",
          comparability: "not_directly_comparable",
          possible_explanations: ["Different benchmark regimes, split strategies, and noise models."],
          confidence: "medium",
        },
      ];

  const gaps = isActuallyLive && bundle.gaps.length > 0
    ? bundle.gaps
    : [
        {
          id: "gap-1",
          scope_kind: "combination",
          subject: { components: ["self-supervised", "noisy forecasting"] },
          saturation_bucket: "limited_evidence_found" as const,
          standardized_language: "Limited evidence of this combination was found within the retrieved and analysed corpus.",
          coverage_disclosure: {},
          evidence_basis: {},
        },
      ];

  const collisions = isActuallyLive && bundle.collisions.length > 0
    ? bundle.collisions
    : [
        {
          id: "col-1",
          component_ids: ["attention routing", "forecasting", "noise robustness"],
          level: "moderately_represented" as const,
          evidence_count: 2,
          explanation: "The combination appears in several retrieved items.",
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
          explanation: "Strong overlap signals in Transformer architecture suggest high research crowding.",
          evidence_ids: [],
          recommendation: "Narrow the differentiator to the exact mathematical operator and evaluation protocol.",
        },
        {
          id: "st-2",
          category: "dataset_availability",
          severity: "medium" as const,
          explanation: "Benchmark datasets exhibit non-standardized split protocols across venues.",
          evidence_ids: [],
          recommendation: "Lock a benchmark suite and report harmonization steps before comparing results.",
        },
      ];

  const differentiations = isActuallyLive && bundle.differentiation.length > 0
    ? bundle.differentiation
    : [
        {
          id: "diff-1",
          overlap_summary: "Strongest overlap is on the 'method' and 'technology' dimensions.",
          overlap_evidence_ids: [],
          differentiation_hypothesis: "A tightly scoped contribution on noise-resilient routing under a disciplined evaluation protocol is a defensible direction.",
          rationale: "Crowding is high on generic architecture, while noise-regime verification is less represented.",
          less_represented_area: "Joint evaluation of noise perturbation and long-horizon efficiency.",
          supporting_evidence_ids: [],
          remaining_uncertainty: "These signals are corpus-dependent and do not establish novelty, absence of prior work, or freedom to operate.",
        },
      ];

  const report = bundle?.report;

  return (
    <section id="workspace" className="mx-auto max-w-7xl px-6 pb-28">
      {/* Header bar */}
      <div className="mb-5 flex flex-wrap items-end justify-between gap-4 border-b border-white/10 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span
              className={`inline-block h-2.5 w-2.5 rounded-full ${
                isActuallyLive ? "bg-emerald-400 shadow-[0_0_12px_#34d399]" : "bg-amber-400"
              }`}
            />
            <p className="text-xs font-semibold tracking-[.25em] text-cyan-300">
              {isActuallyLive ? `LIVE RESEARCH ENGINE · RUN ${bundle.run.id.slice(0, 8)}` : "DEMO / SIMULATED CORPUS"}
            </p>
          </div>
          <h2 className="mt-2 text-3xl font-medium">Research Intelligence Workspace</h2>
        </div>
        <div className="text-right text-xs text-slate-400">
          <div className="font-mono text-[11px] text-slate-500">
            {isActuallyLive ? `STAGE: ${bundle.run.current_stage ?? "COMPLETED"}` : "MODE: OFFLINE DEMO BASELINE"}
          </div>
          <p className="mt-1 text-slate-500">
            Scope-aware · evidence-linked · no novelty guarantees
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto border-b border-white/10 pb-2">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActive(tab)}
            className={`whitespace-nowrap rounded-full px-4 py-2 text-xs font-medium transition ${
              active === tab
                ? "bg-white text-black shadow-md"
                : "text-slate-400 hover:bg-white/5 hover:text-white"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* 1. OVERVIEW TAB */}
      {active === "Overview" && (
        <div className="mt-6 space-y-6">
          <div className="grid gap-4 lg:grid-cols-[1.3fr_.7fr]">
            <div className="glass rounded-3xl p-6">
              <div className="flex items-start justify-between gap-6">
                <div>
                  <div className="text-xs uppercase tracking-[.2em] text-slate-500">
                    Primary Idea
                  </div>
                  <h3 className="mt-2 text-2xl font-medium text-slate-100">{ideaTitle}</h3>
                  <p className="mt-3 text-sm leading-6 text-slate-400">{ideaDesc}</p>
                </div>
                <span
                  className={`rounded-full border px-3 py-1 text-xs uppercase font-medium ${
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
                    className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300"
                  >
                    {x}
                  </span>
                ))}
              </div>
            </div>

            {/* Decision Signal card */}
            <div className="glass rounded-3xl p-6">
              <div className="text-xs uppercase tracking-[.2em] text-slate-500">
                Decision Signal
              </div>
              <div className="mt-6 text-6xl font-semibold text-white">
                {decisionSignal}
                <span className="text-2xl text-slate-500"> / 100</span>
              </div>
              <p className="mt-2 text-sm text-slate-400">
                Analytical opportunity indicator — not an originality proof.
              </p>
              <div className="mt-6 h-2 rounded-full bg-white/5">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-amber-300"
                  style={{ width: `${decisionSignal}%` }}
                />
              </div>
              <p className="mt-4 text-xs leading-5 text-slate-500">
                {bundle?.run?.disclosure ??
                  "Scope-aware signals only: similarity never equals plagiarism, and limited evidence never proves novelty."}
              </p>
            </div>
          </div>

          {/* Structured Idea Decomposition Section */}
          {bundle?.run?.decomposition && (
            <div className="glass rounded-3xl p-6">
              <h4 className="text-sm font-semibold uppercase tracking-[.2em] text-cyan-300">
                Structured Idea Decomposition (8 Dimensions)
              </h4>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="text-xs font-semibold text-slate-400">PROBLEM</div>
                  <p className="mt-1 text-sm text-slate-200">{bundle.run.decomposition.problem}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="text-xs font-semibold text-slate-400">OBJECTIVE</div>
                  <p className="mt-1 text-sm text-slate-200">{bundle.run.decomposition.objective}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="text-xs font-semibold text-slate-400">ARCHITECTURE</div>
                  <p className="mt-1 text-sm text-slate-200">{bundle.run.decomposition.architecture}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="text-xs font-semibold text-slate-400">EXTRACTED CLAIMS</div>
                  <ul className="mt-1 list-disc pl-4 text-xs text-slate-300 space-y-1">
                    {bundle.run.decomposition.claims?.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {bundle.run.decomposition.research_questions && (
                <div className="mt-4 rounded-2xl border border-cyan-500/20 bg-cyan-500/5 p-4">
                  <div className="text-xs font-semibold text-cyan-300">CORE RESEARCH QUESTIONS</div>
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
        <Panel title="Multidimensional Similarity Analysis">
          <div className="grid gap-4 md:grid-cols-2">
            {similarities.map((s) => (
              <div key={s.dimension} className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-semibold capitalize text-slate-200">{s.dimension}</span>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full border border-cyan-400/30 px-2 py-0.5 text-[10px] text-cyan-300 uppercase">
                      {s.confidence} conf
                    </span>
                    <span className="font-mono font-medium text-cyan-200">
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
                <p className="mt-3 text-xs leading-5 text-slate-400">{s.explanation}</p>
                {s.evidence_ids && s.evidence_ids.length > 0 && (
                  <div className="mt-3 text-[11px] text-slate-500">
                    Linked evidence: {s.evidence_ids.map((x) => String(x).slice(0, 8)).join(", ")}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* 3. EVIDENCE TAB */}
      {active === "Evidence" && (
        <Panel title="Evidence Chain (Conclusion → Claim → Excerpt → Source)">
          <div className="space-y-4">
            {evidences.map((ev, i) => (
              <div key={ev.id || i} className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="rounded-md border border-cyan-400/30 bg-cyan-400/10 px-2 py-0.5 text-[10px] font-semibold uppercase text-cyan-300">
                      {ev.dimension}
                    </span>
                    <span className="text-xs font-medium text-slate-300">
                      {ev.claim_text}
                    </span>
                  </div>
                  <span className="text-[11px] uppercase tracking-wider text-slate-500">
                    Strength: {ev.strength} · Conf: {ev.extraction_confidence}
                  </span>
                </div>

                <div className="mt-3 rounded-xl border border-white/5 bg-black/40 p-3 font-serif text-xs italic leading-6 text-slate-300">
                  &ldquo;{ev.excerpt}&rdquo;
                </div>

                {ev.provenance_backref && (
                  <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400">
                    <span>Source: {ev.provenance_backref.title || "Academic Source"}</span>
                    {ev.provenance_backref.url && (
                      <a
                        href={ev.provenance_backref.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-cyan-400 hover:underline"
                      >
                        Open Source Paper / Repo ↗
                      </a>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* 4. SOURCES TAB */}
      {active === "Sources" && (
        <Panel title="Retrieved & Normalized Sources (arXiv, Semantic Scholar, Crossref, GitHub)">
          <div className="grid gap-4 md:grid-cols-2">
            {sources.map((src) => (
              <div key={src.id} className="flex flex-col justify-between rounded-2xl border border-white/10 bg-white/5 p-5">
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="rounded-full border border-white/15 px-2.5 py-0.5 text-[10px] font-mono uppercase text-slate-300">
                      {src.adapter_id}
                    </span>
                    <span className="text-xs text-slate-500">{src.year ?? "Recent"}</span>
                  </div>
                  <h4 className="mt-3 text-sm font-medium text-slate-100">{src.title}</h4>
                  <p className="mt-2 text-xs text-slate-400">
                    {src.authors?.slice(0, 3).join(", ") || "Authors reported in paper"}
                    {src.venue ? ` · ${src.venue}` : ""}
                  </p>
                </div>

                <div className="mt-4 flex items-center justify-between border-t border-white/10 pt-3 text-[11px]">
                  <span className="font-mono text-slate-500">{src.dedup_status}</span>
                  {src.primary_url ? (
                    <a
                      href={src.primary_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-300 hover:underline"
                    >
                      Canonical Reference ↗
                    </a>
                  ) : (
                    <span className="text-slate-600">No URL</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* 5. COVERAGE TAB */}
      {active === "Coverage" && (
        <Panel title="Research Coverage Map (Per-Dimension Sufficiency)">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {coverages.map((c) => (
              <div key={c.dimension} className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <div className="flex justify-between text-sm">
                  <span className="font-semibold capitalize text-slate-200">{c.dimension}</span>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-[10px] uppercase font-medium ${
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
                <p className="mt-3 text-xs leading-5 text-slate-400">{c.explanation}</p>
                <div className="mt-4 border-t border-white/10 pt-2 text-[11px] text-slate-500">
                  {c.evidence_count} evidence records · {c.source_count} sources
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
                  <span className="text-xs font-semibold tracking-[.2em] text-amber-300 uppercase">
                    CONFLICT OBSERVATION · {con.dimension}
                  </span>
                  <span className="rounded-full border border-amber-400/30 px-2 py-0.5 text-[10px] text-amber-200">
                    Comparability: {con.comparability}
                  </span>
                </div>
                <h4 className="mt-3 text-base font-medium text-slate-100">{con.subject}</h4>
                <p className="mt-2 text-sm leading-6 text-slate-300">{con.conflict_summary}</p>
                {con.possible_explanations && (
                  <div className="mt-4 rounded-xl border border-white/10 bg-black/40 p-3 text-xs text-slate-400">
                    <span className="font-semibold text-slate-200">Possible Explanations: </span>
                    {con.possible_explanations.join(" ")}
                  </div>
                )}
                <div className="mt-3 text-[11px] text-amber-300/80">
                  Neither side is eliminated; both experimental paradigms are cataloged for review.
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
                  <div className="text-sm font-medium text-slate-100">
                    {gap.subject.dimension
                      ? `Dimension: ${gap.subject.dimension}`
                      : `Combination: ${gap.subject.components?.join(" × ")}`}
                  </div>
                  <p className="mt-1 text-xs text-slate-400">{gap.standardized_language}</p>
                </div>
                <span className="mt-2 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs text-cyan-300 md:mt-0">
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
          <div className="grid gap-4 md:grid-cols-2">
            {collisions.map((col, idx) => (
              <div key={col.id || idx} className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <div className="text-sm font-medium text-slate-100">
                  {col.component_ids.join("  ×  ")}
                </div>
                <p className="mt-2 text-xs text-slate-400">{col.explanation}</p>
                <div className="mt-4 flex items-center justify-between border-t border-white/10 pt-2 text-[11px] text-slate-500">
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
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {stressTests.map((st, i) => (
              <div key={st.id || i} className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase font-semibold text-slate-400">
                    {st.category.replace(/_/g, " ")}
                  </span>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ${
                      st.severity === "high" || st.severity === "critical"
                        ? "bg-rose-400/10 text-rose-300 border border-rose-400/30"
                        : "bg-amber-400/10 text-amber-300 border border-amber-400/30"
                    }`}
                  >
                    {st.severity}
                  </span>
                </div>
                <p className="mt-3 text-xs leading-5 text-slate-300">{st.explanation}</p>
                <div className="mt-4 rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-3 text-xs text-cyan-200">
                  <span className="font-semibold text-white">Action: </span>
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
          <div className="space-y-4">
            {differentiations.map((diff, i) => (
              <div key={diff.id || i} className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                  <div className="text-xs uppercase font-semibold text-slate-400">OVERLAP REGION</div>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{diff.overlap_summary}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                  <div className="text-xs uppercase font-semibold text-slate-400">LESS REPRESENTED ANGLE</div>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{diff.less_represented_area}</p>
                </div>
                <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/5 p-5 md:col-span-2">
                  <div className="text-xs uppercase font-semibold text-cyan-300">DIFFERENTIATION HYPOTHESIS</div>
                  <p className="mt-2 text-base text-slate-100">{diff.differentiation_hypothesis}</p>
                  <p className="mt-2 text-xs leading-5 text-slate-400">{diff.rationale}</p>
                  <div className="mt-4 border-t border-white/10 pt-2 text-[11px] text-amber-300">
                    Caveat: {diff.remaining_uncertainty}
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
    <div className="glass mt-6 rounded-3xl p-6">
      <h3 className="text-xl font-medium text-slate-100">{title}</h3>
      <div className="mt-5">{children}</div>
    </div>
  );
}
