import type {
  ResearchRun, Source, Evidence, Claim, SimilarityResult, CoverageResult,
  Contradiction, ResearchGap, CollisionCombination, StressTest, Differentiation,
  GraphNode, GraphEdge, Report
} from "../types/domain";

export interface ResearchRunRepository {
  createRun(ideaId: string): Promise<ResearchRun>;
  getRun(runId: string): Promise<ResearchRun | null>;
  listRuns(ideaId: string): Promise<ResearchRun[]>;
}
export interface SourceRepository {
  getSources(runId: string): Promise<Source[]>;
  getSourceById(sourceId: string): Promise<Source | null>;
}
export interface EvidenceRepository {
  getClaims(runId: string): Promise<Claim[]>;
  getEvidenceForClaim(claimId: string): Promise<Evidence[]>;
  getEvidenceById(evidenceId: string): Promise<Evidence | null>;
}
export interface AnalysisRepository {
  getSimilarities(runId: string): Promise<SimilarityResult[]>;
  getCoverage(runId: string): Promise<CoverageResult[]>;
  getContradictions(runId: string): Promise<Contradiction[]>;
  getGaps(runId: string): Promise<ResearchGap[]>;
  getCollisions(runId: string): Promise<CollisionCombination[]>;
  getStressTests(runId: string): Promise<StressTest[]>;
  getDifferentiation(runId: string): Promise<Differentiation[]>;
}
export interface GraphRepository {
  getNodes(runId: string): Promise<GraphNode[]>;
  getEdges(runId: string): Promise<GraphEdge[]>;
}
export interface ReportRepository { getReport(runId: string): Promise<Report | null>; }