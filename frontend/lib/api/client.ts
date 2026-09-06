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
const TOKEN_STORAGE_KEY = "idealens_auth_token";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

/**
 * Acquire or refresh an authentication session token from the backend.
 */
export async function acquireSessionToken(userId?: string): Promise<string> {
  const targetId = userId || `researcher-${Math.random().toString(36).substring(2, 9)}`;
  const response = await fetch(`${API_BASE}/api/v1/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: targetId }),
  });
  if (!response.ok) {
    throw new Error(`Auth service returned status ${response.status}`);
  }
  const data = await response.json();
  const token = data.access_token as string;
  setStoredToken(token);
  return token;
}

export function getAuthHeaders(extraHeaders: Record<string, string> = {}): HeadersInit {
  const headers: Record<string, string> = { ...extraHeaders };
  const token = getStoredToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export interface ResearchRunSummaryItem {
  id: string;
  status: "queued" | "running" | "completed" | "partially_failed" | "failed";
  idea: string;
  title?: string | null;
  progress: number;
  current_stage?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  disclosure: string;
  decision_signal: number;
  sources_count: number;
  evidence_count: number;
}

/**
 * Upload a document (TXT, PDF, DOCX) and extract plain text.
 */
export async function uploadDocument(file: File): Promise<DocumentUploadResult> {
  const formData = new FormData();
  formData.append("file", file);

  let headers: HeadersInit = {};
  const token = getStoredToken();
  if (token) {
    headers = { Authorization: `Bearer ${token}` };
  }

  let response = await fetch(`${API_BASE}/api/v1/documents/upload`, {
    method: "POST",
    headers,
    body: formData,
  });

  // If auth is strictly enforced and no/invalid token was sent, acquire session and retry
  if (response.status === 401) {
    try {
      const newToken = await acquireSessionToken();
      response = await fetch(`${API_BASE}/api/v1/documents/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${newToken}` },
        body: formData,
      });
    } catch {
      // Proceed to normal error handling
    }
  }

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
    let message = "Document upload failed";
    let code = "UPLOAD_FAILED";
    if (typeof err.detail === "string") {
      message = err.detail;
    } else if (err.detail && typeof err.detail === "object") {
      message = err.detail.message || JSON.stringify(err.detail);
      code = err.detail.code || code;
    }
    const customError = new Error(message);
    (customError as unknown as { code: string }).code = code;
    throw customError;
  }
  return (await response.json()) as DocumentUploadResult;
}

/**
 * List previous research runs from the backend database.
 */
export async function listResearchRuns(limit = 25): Promise<ResearchRunSummaryItem[]> {
  try {
    const response = await fetch(`${API_BASE}/api/v1/research-runs?limit=${limit}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) return [];
    const data = await response.json();
    return (data.items || []) as ResearchRunSummaryItem[];
  } catch (err) {
    console.warn("Could not load research history from API:", err);
    return [];
  }
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
    let response = await fetch(`${API_BASE}/api/v1/research-runs`, {
      method: "POST",
      headers: getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        idea,
        document_id: documentId || null,
      }),
      signal: controller.signal,
    });

    if (response.status === 401) {
      const newToken = await acquireSessionToken();
      response = await fetch(`${API_BASE}/api/v1/research-runs`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${newToken}`,
        },
        body: JSON.stringify({
          idea,
          document_id: documentId || null,
        }),
        signal: controller.signal,
      });
    }

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
  const response = await fetch(`${API_BASE}/api/v1/research-runs/${runId}`, {
    headers: getAuthHeaders(),
  });
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
  const headers = getAuthHeaders();

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
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/sources`, { headers }).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/evidence`, { headers }).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/similarity`, { headers }).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/coverage`, { headers }).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/contradictions`, { headers }).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/gaps`, { headers }).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/collisions`, { headers }).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/stress-tests`, { headers }).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/differentiation`, { headers }).then((r) => r.ok ? r.json() : []),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/graph`, { headers }).then((r) => r.ok ? r.json() : null),
    fetch(`${API_BASE}/api/v1/research-runs/${runId}/report`, { headers }).then((r) => r.ok ? r.json() : null),
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
