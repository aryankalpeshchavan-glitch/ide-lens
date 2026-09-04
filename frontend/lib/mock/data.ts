import type {
  Idea, Source, Evidence, SimilarityResult, CoverageResult,
  Contradiction, ResearchGap, CollisionCombination, StressTest, Differentiation
} from "../types/domain";

export const DEMO_IDEA: Idea = {
  id: "idea_demo_01",
  title: "Quantum-Inspired Attention Mechanisms for Time-Series Forecasting",
  description: "A research concept exploring alternative attention normalization for long-horizon time-series forecasting.",
  technologies: ["Transformers", "PyTorch", "Time-Series", "Quantum-inspired methods"],
  researchQuestions: [
    "Does the proposed normalization reduce computational overhead?",
    "How does it behave on noisy high-frequency sequences?"
  ],
  createdAt: new Date().toISOString()
};

export const SOURCES: Source[] = [
  { id: "src01", title: "Non-Classical Attention in Sequential Models", authors: ["Demo Research Group"], publicationDate: "2025-01-15", sourceType: "academic_paper", identifier: "demo:paper:01", metadata: { method: ["Literature review"], technology: ["Transformers"] } },
  { id: "src02", title: "qia-ts-experimental-repository", authors: ["Demo Systems"], publicationDate: "2025-03-20", sourceType: "github_repository", identifier: "demo/qia-ts", metadata: { dataset: ["Synthetic high-frequency sequences"], limitations: "Sensitivity increases under severe missingness." } },
  { id: "src03", title: "Long-Horizon Forecasting Benchmark", authors: ["Benchmark Team"], publicationDate: "2024-11-02", sourceType: "technical_source", identifier: "demo:benchmark:03", metadata: { dataset: ["Multivariate forecasting"], results: "Useful baseline comparison context." } }
];

export const EVIDENCE: Evidence[] = [
  { id: "ev01", claimId: "claim01", sourceId: "src01", excerpt: "Theoretical analysis indicates an alternative routing strategy can reduce the asymptotic work performed per sequence.", evidenceType: "paraphrased_finding", dimensions: ["architecture", "method"], confidence: .85, location: "Section 3" },
  { id: "ev02", claimId: "claim02", sourceId: "src02", excerpt: "Training becomes unstable when the signal-to-noise ratio falls below a threshold in the demonstration setup.", evidenceType: "statistical_result", dimensions: ["evaluation"], confidence: .92, location: "README / Known Issues" },
  { id: "ev03", claimId: "claim03", sourceId: "src03", excerpt: "Long-horizon evaluation is strongly affected by sequence length, data regime, and metric selection.", evidenceType: "paraphrased_finding", dimensions: ["evaluation", "dataset"], confidence: .81, location: "Benchmark notes" }
];

export const SIMILARITIES: SimilarityResult[] = [
  { dimension: "problem", score: .74, confidence: .83, explanation: "The retrieved corpus repeatedly targets long-horizon forecasting under compute constraints.", evidenceIds: ["ev01","ev03"] },
  { dimension: "technology", score: .88, confidence: .94, explanation: "Transformer-based sequence models dominate the retrieved technical space.", evidenceIds: ["ev01"] },
  { dimension: "method", score: .63, confidence: .76, explanation: "Alternative attention/routing strategies recur, but the exact normalization pattern is less represented.", evidenceIds: ["ev01"] },
  { dimension: "architecture", score: .58, confidence: .72, explanation: "The architecture overlaps with attention-based sequence pipelines while differing at the attention block.", evidenceIds: ["ev01","ev03"] },
  { dimension: "dataset", score: .47, confidence: .67, explanation: "The evidence spans synthetic and benchmark datasets rather than a single dominant corpus.", evidenceIds: ["ev02","ev03"] },
  { dimension: "domain", score: .69, confidence: .79, explanation: "The strongest overlap is with forecasting and noisy sequential signals.", evidenceIds: ["ev02","ev03"] }
];

export const COVERAGE: CoverageResult[] = [
  { dimension: "problem", level: "strong", explanation: "Well represented across the retrieved corpus.", evidenceCount: 3, sourceCount: 3, confidence: .9 },
  { dimension: "technology", level: "strong", explanation: "Transformer usage is highly represented.", evidenceCount: 2, sourceCount: 2, confidence: .94 },
  { dimension: "method", level: "moderate", explanation: "Alternative attention mechanisms are present but heterogeneous.", evidenceCount: 2, sourceCount: 2, confidence: .78 },
  { dimension: "architecture", level: "moderate", explanation: "Architectural evidence is available but not standardized.", evidenceCount: 2, sourceCount: 2, confidence: .73 },
  { dimension: "dataset", level: "limited", explanation: "Dataset overlap is fragmented across benchmark contexts.", evidenceCount: 1, sourceCount: 1, confidence: .64 },
  { dimension: "evaluation", level: "moderate", explanation: "Evaluation evidence is present but sensitive to protocol.", evidenceCount: 2, sourceCount: 2, confidence: .75 }
];

export const CONTRADICTIONS: Contradiction[] = [
  { id: "con01", claimId: "claim02", evidenceAId: "ev01", evidenceBId: "ev02", sourceAId: "src01", sourceBId: "src02", conflictingValues: "One source suggests robustness while the experimental repository reports instability under severe noise.", possibleExplanation: "Different data regimes, model versions, and noise protocols.", confidence: .78 }
];

export const GAPS: ResearchGap[] = [
  { area: "Alternative attention on noisy long-horizon forecasting", level: "limited_evidence_found", explanation: "Few directly comparable items were found in the current search scope.", evidenceCount: 2, sourceCount: 2, confidence: .69, searchScope: "Demo corpus only" },
  { area: "Transformer baselines for forecasting", level: "common", explanation: "Strongly represented in the corpus.", evidenceCount: 8, sourceCount: 5, confidence: .93, searchScope: "Demo corpus only" }
];

export const COLLISIONS: CollisionCombination[] = [
  { componentIds: ["transformers","attention","forecasting"], level: "moderately_represented", evidenceCount: 4, explanation: "The broad combination is represented by multiple related works.", confidence: .84 },
  { componentIds: ["alternative-normalization","noisy-forecasting","long-horizon"], level: "limited_evidence_found", evidenceCount: 1, explanation: "The exact multi-component combination appears less represented in this demo corpus.", confidence: .66 }
];

export const STRESS: StressTest[] = [
  { category: "research_saturation", severity: "high", explanation: "The broad problem area has substantial prior work.", evidenceIds: ["ev01","ev03"], recommendation: "Narrow the differentiator to the exact mechanism and evaluation protocol." },
  { category: "dataset_availability", severity: "medium", explanation: "Comparable datasets exist, but apples-to-apples evaluation may require harmonization.", evidenceIds: ["ev03"], recommendation: "Lock a benchmark suite before claiming improvement." },
  { category: "evaluation_difficulty", severity: "high", explanation: "Results are sensitive to noise regime, horizon, and metric selection.", evidenceIds: ["ev02","ev03"], recommendation: "Publish protocol, splits, and ablations." }
];

export const DIFFERENTIATION: Differentiation = {
  overlap: "Transformer-based long-horizon forecasting with alternative attention computation.",
  lessRepresentedArea: "Joint treatment of alternative normalization, noisy signals, and long-horizon evaluation.",
  technicalMeaning: "The opportunity is a tighter mechanism + evaluation protocol rather than a generic new transformer.",
  opportunity: "Design controlled ablations that isolate the normalization mechanism from architecture and data effects.",
  evidenceIds: ["ev01","ev02","ev03"],
  uncertainty: "Limited-evidence signals are corpus-dependent and do not establish novelty or freedom to operate."
};