import type {
  AnalysisRepository, EvidenceRepository, ResearchRunRepository, SourceRepository
} from "../api/interfaces";
import type { ResearchRun } from "../types/domain";
import {
  DEMO_IDEA, SOURCES, EVIDENCE, SIMILARITIES, COVERAGE, CONTRADICTIONS,
  GAPS, COLLISIONS, STRESS, DIFFERENTIATION
} from "./data";

export class MockResearchRunRepository implements ResearchRunRepository {
  private run: ResearchRun | null = null;
  async createRun(ideaId: string) {
    this.run = {
      id: "run_demo_01",
      ideaId,
      status: "completed",
      createdAt: new Date().toISOString(),
      progress: 100,
      currentStage: "report_generation",
      stages: [
        "decomposition","query_generation","retrieval","normalization",
        "evidence_extraction","similarity_analysis","graph_construction",
        "contradiction_analysis","gap_analysis","collision_analysis",
        "differentiation","report_generation"
      ]
    };
    return this.run;
  }
  async getRun(runId: string) { return this.run?.id === runId ? this.run : null; }
  async listRuns(ideaId: string) { return this.run?.ideaId === ideaId && this.run ? [this.run] : []; }
}

export class MockSourceRepository implements SourceRepository {
  async getSources() { return SOURCES; }
  async getSourceById(id: string) { return SOURCES.find(x => x.id === id) ?? null; }
}

export class MockEvidenceRepository implements EvidenceRepository {
  async getClaims() {
    return [
      { id: "claim01", text: "Alternative attention routing may reduce compute." },
      { id: "claim02", text: "Noise can destabilize training." },
      { id: "claim03", text: "Evaluation protocol materially affects conclusions." }
    ];
  }
  async getEvidenceForClaim(id: string) { return EVIDENCE.filter(x => x.claimId === id); }
  async getEvidenceById(id: string) { return EVIDENCE.find(x => x.id === id) ?? null; }
}

export class MockAnalysisRepository implements AnalysisRepository {
  async getSimilarities() { return SIMILARITIES; }
  async getCoverage() { return COVERAGE; }
  async getContradictions() { return CONTRADICTIONS; }
  async getGaps() { return GAPS; }
  async getCollisions() { return COLLISIONS; }
  async getStressTests() { return STRESS; }
  async getDifferentiation() { return [DIFFERENTIATION]; }
}

export const MOCK = {
  idea: DEMO_IDEA,
  sources: new MockSourceRepository(),
  evidence: new MockEvidenceRepository(),
  analysis: new MockAnalysisRepository(),
  runs: new MockResearchRunRepository()
};