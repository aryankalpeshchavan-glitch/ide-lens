export interface DocumentMetadata {
  filename: string; mimeType: string; sizeBytes: number; backendId?: string;
}
export interface Idea {
  id: string; title: string; description: string; technologies: string[];
  researchQuestions: string[]; createdAt: string; documentMetadata?: DocumentMetadata;
}
export type ResearchRunStatus = "idle" | "queued" | "running" | "completed" | "partial" | "failed";
export type ResearchStage =
  | "decomposition" | "query_generation" | "retrieval" | "normalization"
  | "evidence_extraction" | "similarity_analysis" | "graph_construction"
  | "contradiction_analysis" | "gap_analysis" | "collision_analysis"
  | "differentiation" | "report_generation";
export interface ResearchRun {
  id: string; ideaId: string; status: ResearchRunStatus; createdAt: string;
  startedAt?: string; completedAt?: string; progress: number;
  currentStage?: ResearchStage; stages: ResearchStage[]; error?: string; partialFailures?: string[];
}
export type SourceType = "academic_paper" | "github_repository" | "dataset" | "technical_source" | "other";
export interface SourceMetadata {
  method?: string[]; technology?: string[]; dataset?: string[];
  results?: string; limitations?: string;
}
export interface Source {
  id: string; title: string; authors: string[]; publicationDate: string;
  sourceType: SourceType; url?: string; identifier?: string; metadata: SourceMetadata;
}
export type EvidenceDimension = "problem" | "objective" | "technology" | "method" | "architecture" | "dataset" | "evaluation";
export interface Claim { id: string; text: string; }
export interface Evidence {
  id: string; claimId: string; sourceId: string; excerpt: string;
  evidenceType: "direct_quote" | "paraphrased_finding" | "statistical_result";
  dimensions: EvidenceDimension[]; confidence: number; location?: string;
}
export type SimilarityDimension = "problem" | "objective" | "technology" | "method" | "architecture" | "dataset" | "domain";
export interface SimilarityResult {
  dimension: SimilarityDimension; score: number; confidence: number;
  explanation: string; evidenceIds: string[];
}
export type CoverageLevel = "strong" | "moderate" | "limited" | "insufficient";
export interface CoverageResult {
  dimension: EvidenceDimension; level: CoverageLevel; explanation: string;
  evidenceCount: number; sourceCount: number; confidence: number;
}
export interface Contradiction {
  id: string; claimId: string; evidenceAId: string; evidenceBId: string;
  sourceAId: string; sourceBId: string; conflictingValues: string;
  possibleExplanation: string; confidence: number;
}
export interface ResearchGap {
  area: string; level: "common" | "moderately_represented" | "limited_evidence_found" | "insufficient_evidence";
  explanation: string; evidenceCount: number; sourceCount: number; confidence: number; searchScope: string;
}
export interface CollisionCombination {
  componentIds: string[];
  level: "common" | "moderately_represented" | "limited_evidence_found" | "insufficient_evidence";
  evidenceCount: number; explanation: string; confidence: number;
}
export interface StressTest {
  category: "alternative_approaches" | "research_saturation" | "dataset_availability" | "evaluation_difficulty" | "deployment_constraints" | "unsupported_assumptions" | "evidence_weaknesses";
  severity: "low" | "medium" | "high" | "critical";
  explanation: string; evidenceIds: string[]; recommendation?: string;
}
export interface Differentiation {
  overlap: string; lessRepresentedArea: string; technicalMeaning: string;
  opportunity: string; evidenceIds: string[]; uncertainty: string;
}
export interface GraphNode { id: string; type: string; label: string; referenceId?: string; }
export interface GraphEdge { id: string; sourceNodeId: string; targetNodeId: string; relationshipType: string; confidence: number; }
export interface Report {
  id: string; runId: string; executiveSummary: string; ideaDecomposition: string;
  researchScope: string; methodology: string; limitations: string;
  coverageIds: string[]; similarityIds: string[]; contradictionIds: string[];
  gapIds: string[]; collisionIds: string[]; stressTestIds: string[]; differentiationIds: string[];
}