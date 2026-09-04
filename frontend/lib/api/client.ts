/**
 * IdeaLens API Client
 * Strongly typed service boundary connecting frontend components to FastAPI backend.
 */

export interface DecompositionData {
  problem?: string;
  objective?: string;
  technologies?: string[];
  methods?: string[];
  datasets?: string[];
  architecture?: string;
  claims?: string[];
  research_questions?: string[];
  keywords?: string[];
  dimensions?: Record<string, string[]>;
  concepts?: string[];
}

export interface ResearchRunResult {
  id: string;
  status: "queued" | "running" | "completed" | "partially_failed" | "failed";
  idea: string;
  progress: number;
  current_stage?: string | null;
  decision_signal: number;
  sources_count: number;
  evidence_count: number;
  disclosure: string;
  next_steps: string[];
  source_document_id?: string | null;
  decomposition?: DecompositionData | null;
  error_summary?: Array<{ class: string; stage?: string; message: string }>;
  created_at?: string;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface DocumentUploadResult {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  hash_sha256: string;
  extracted_title: string | null;
  extracted_text: string;
  word_count: number;
  chunks_count: number;
  doc_metadata: Record<string, unknown>;
}

export interface SourceItem {
  id: string;
  adapter_id: string;
  source_kind: string;
  title: string;
  authors: string[];
  venue?: string | null;
  year?: number | null;
  primary_url?: string | null;
  identifiers: Record<string, string>;
  dedup_status: string;
  quality_signals: Record<string, unknown>;
  retrieved_at: string;
}

export interface EvidenceItem {
  id: string;
  source_item_id: string;
  dimension: string;
  claim_text: string;
  excerpt: string;
  extraction_confidence: string;
  provenance_backref?: { url?: string; title?: string; identifiers?: Record<string, string> } | null;
  strength: string;
}

export interface SimilarityItem {
  id: string;
  dimension: string;
  score: number;
  confidence: string;
  explanation: string;
  evidence_ids: string[];
  lexical_score?: number | null;
  structured_score?: number | null;
}

export interface CoverageItem {
  id: string;
  dimension: string;
  level: "strong" | "moderate" | "limited" | "insufficient";
  explanation: string;
  evidence_count: number;
  source_count: number;
  confidence: string;
}

export interface ContradictionItem {
  id: string;
  dimension: string;
  subject: string;
  evidence_a_id?: string | null;
  evidence_b_id?: string | null;
  source_a_id?: string | null;
  source_b_id?: string | null;
  comparability: string;
  conflict_summary: string;
  possible_explanations?: string[] | null;
  confidence: string;
}

export interface GapItem {
  id: string;
  scope_kind: string;
  subject: { dimension?: string; components?: string[] };
  saturation_bucket: "common" | "moderately_represented" | "limited_evidence_found" | "insufficient_evidence";
  standardized_language: string;
  coverage_disclosure: { queries_planned?: number; queries_executed?: number; coverage_degraded?: boolean };
  evidence_basis: { evidence_ids?: string[]; evidence_count?: number };
}

export interface CollisionItem {
  id: string;
  component_ids: string[];
  level: "common" | "moderately_represented" | "limited_evidence_found" | "insufficient_evidence";
  evidence_count: number;
  explanation: string;
  confidence: string;
}

export interface StressTestItem {
  id: string;
  category: string;
  severity: "low" | "medium" | "high" | "critical";
  explanation: string;
  evidence_ids: string[];
  recommendation: string;
}

export interface DifferentiationItem {
  id: string;
  overlap_summary: string;
  overlap_evidence_ids: string[];
  differentiation_hypothesis: string;
  rationale: string;
  less_represented_area: string;
  supporting_evidence_ids: string[];
  remaining_uncertainty: string;
}

export interface GraphNode {
  id: string;
  node_type: string;
  label: string;
  reference_id?: string | null;
  meta?: Record<string, unknown> | null;
}

export interface GraphEdge {
  id: string;
  source_node_id: string;
  target_node_id: string;
  relationship_type: string;
  weight?: number | null;
  confidence: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ReportData {
  id: string;
  format: string;
  content: string;
  citations?: Record<string, unknown> | null;
  scope_disclosure?: Record<string, unknown> | null;
  language_guardrail_status: string;
  generated_at: string;
}

export interface RunArtifactsBundle {
  run: ResearchRunResult;
  sources: SourceItem[];
  evidence: EvidenceItem[];
  similarity: SimilarityItem[];
  coverage: CoverageItem[];
  contradictions: ContradictionItem[];
  gaps: GapItem[];
  collisions: CollisionItem[];
  stressTests: StressTestItem[];
  differentiation: DifferentiationItem[];
  graph: GraphData | null;
  report: ReportData | null;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

/**
 * Upload a document (TXT, PDF, DOCX) and extract plain text.
 */
export async function uploadDocument(file: File): Promise<DocumentUploadResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/v1/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
    throw new Error(err.detail || "Document upload failed");
  }
  return (await response.json()) as DocumentUploadResult;
}

/**
 * Create an asynchronous research run.
 */
export async function createResearchRun(
  idea: string,
  documentId?: string | null
): Promise<ResearchRunResult> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(`${API_BASE}/api/v1/research-runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        idea,
        document_id: documentId || null,
      }),
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`Research API returned ${response.status}`);
    return (await response.json()) as ResearchRunResult;
  } finally {
    window.clearTimeout(timeout);
  }
}

/**
 * Fetch a single research run metadata record.
 */
export async function getResearchRun(runId: string): Promise<ResearchRunResult> {
  const response = await fetch(`${API_BASE}/api/v1/research-runs/${runId}`);
  if (!response.ok) throw new Error(`Failed to fetch run: ${response.status}`);
  return (await response.json()) as ResearchRunResult;
}

/**
 * Poll a research run until completed, partially_failed, or failed.
 */
export async function pollResearchRun(
  runId: string,
  onProgress?: (run: ResearchRunResult) => void,
  maxAttempts = 60,
  intervalMs = 1500
): Promise<ResearchRunResult> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const current = await getResearchRun(runId);
    if (onProgress) onProgress(current);

    if (
      current.status === "completed" ||
      current.status === "partially_failed" ||
      current.status === "failed"
    ) {
      return current;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  return await getResearchRun(runId);
}

/**
 * Fetch all analytical artifacts for a completed run in parallel.
 */
export async function fetchAllRunArtifacts(run: ResearchRunResult): Promise<RunArtifactsBundle> {
  const runId = run.id;

  const [
    sourcesRes,
    evidenceRes,
    simRes,
    covRes,
    conRes,
    gapRes,
    colRes,
    stressRes,
    diffRes,
    graphRes,
    reportRes,
  ] = await Promise.allSettled([
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/sources`).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/evidence`).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/similarity`).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/coverage`).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/contradictions`).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/gaps`).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/collisions`).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/stress-tests`).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/differentiation`).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/graph`).then((r) => r.ok ? r.json() : null),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/report`).then((r) => r.ok ? r.json() : null),
  ]);

  return {
    run,
    sources: sourcesRes.status === "fulfilled" ? (sourcesRes.value as SourceItem[]) : [],
    evidence: evidenceRes.status === "fulfilled" ? (evidenceRes.value as EvidenceItem[]) : [],
    similarity: simRes.status === "fulfilled" ? (simRes.value as SimilarityItem[]) : [],
    coverage: covRes.status === "fulfilled" ? (covRes.value as CoverageItem[]) : [],
    contradictions: conRes.status === "fulfilled" ? (conRes.value as ContradictionItem[]) : [],
    gaps: gapRes.status === "fulfilled" ? (gapRes.value as GapItem[]) : [],
    collisions: colRes.status === "fulfilled" ? (colRes.value as CollisionItem[]) : [],
    stressTests: stressRes.status === "fulfilled" ? (stressRes.value as StressTestItem[]) : [],
    differentiation: diffRes.status === "fulfilled" ? (diffRes.value as DifferentiationItem[]) : [],
    graph: graphRes.status === "fulfilled" ? (graphRes.value as GraphData | null) : null,
    report: reportRes.status === "fulfilled" ? (reportRes.value as ReportData | null) : null,
  };
}
