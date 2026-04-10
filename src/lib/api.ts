export interface OverviewStat {
  name: string;
  value: string;
  trend: string;
  icon: string;
  tone: string;
}

export interface OverviewApp {
  id: string;
  name: string;
  description: string;
  status: string;
  icon: string;
}

export interface OverviewWorkflow {
  id: string;
  name: string;
  status: string;
  runs_today: number;
  latency_ms: number;
}

export interface OverviewActivity {
  id: string;
  type: string;
  name: string;
  action: string;
  time: string;
}

export interface OverviewData {
  product: {
    name: string;
    tagline: string;
  };
  stats: OverviewStat[];
  apps: OverviewApp[];
  workflows: OverviewWorkflow[];
  activities: OverviewActivity[];
}

export interface IntegrationProvider {
  id: string;
  name: string;
  slug: string;
  category: string;
  logo: string;
  accent: string;
  type: "api_key" | "oauth";
  status: "Connected" | "Not Connected";
  connection_id: string | null;
  connection_ref: string | null;
}

export interface IntegrationCategory {
  id: string;
  name: string;
  providers: IntegrationProvider[];
}

export interface IntegrationConnection {
  connection_id: string;
  provider: string;
  type: "api_key" | "oauth";
  status: string;
}

export interface IntegrationStatusResponse {
  provider: string;
  status: "pending" | "connected" | "failed" | "revoked" | "not_connected";
  connection_id: string | null;
  connection_ref: string | null;
}

export interface IntegrationsResponse {
  summary: {
    total: number;
    connected: number;
    disconnected: number;
  };
  categories: IntegrationCategory[];
}

export interface EnvDetectResponse {
  provider: string;
  found: boolean;
  env_key: string | null;
  api_key: string | null;
  masked_key: string | null;
}

export type ApiKeyConnectResponse = IntegrationConnection;

export interface OAuthSessionResponse extends IntegrationConnection {
  status: string;
  connect_session_token: string;
  nango_integration_id: string;
}

export interface KnowledgeBaseDataset {
  id: string;
  name: string;
  slug: string;
  description: string;
  embedding_model: string;
  chunk_size: number;
  document_count: number;
  ready_count: number;
  processing_count: number;
  failed_count: number;
  chunk_count: number;
}

export interface KnowledgeBaseSummary {
  total_datasets: number;
  total_documents: number;
  total_chunks: number;
}

export interface KnowledgeBaseDatasetsResponse {
  datasets: KnowledgeBaseDataset[];
  summary: KnowledgeBaseSummary;
}

export interface KnowledgeBaseDocument {
  id: string;
  dataset_id: string;
  title: string;
  file_name: string;
  mime_type: string;
  file_size: number;
  page_count: number;
  status: "processing" | "ready" | "failed";
  error_message: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeBaseDocumentPage {
  dataset: KnowledgeBaseDataset;
  page: number;
  limit: number;
  total: number;
  documents: KnowledgeBaseDocument[];
}

export interface KnowledgeBaseChunkResult {
  chunk_id: string;
  document_id: string;
  document_title: string;
  page_number: number;
  start_char: number;
  end_char: number;
  text: string;
  score: number;
}

export interface KnowledgeBaseQueryResponse {
  dataset_id: string;
  query: string;
  cached: boolean;
  results: KnowledgeBaseChunkResult[];
}

export interface KnowledgeBaseUploadResponse {
  document_id: string;
  dataset_id: string;
  file_name: string;
  status: "processing" | "ready" | "failed";
  duplicate?: boolean;
}

export interface KnowledgeBaseDeleteResponse {
  document_id: string;
  deleted: boolean;
  removed_chunks: number;
}

export interface KnowledgeBaseSeedResponse {
  datasets_seeded: number;
  documents_seeded: number;
  chunks_indexed: number;
}

export interface WorkflowRetryPolicy {
  max_retries: number;
  backoff: string;
  retry_on: string[];
}

export interface WorkflowNodeDefinition {
  id: string;
  type: string;
  name: string;
  position: { x: number; y: number };
  config: Record<string, unknown>;
  input_mapping?: Record<string, string>;
  output_mapping?: Record<string, string>;
  ai_brain: boolean;
  memory: "short_term" | "long_term" | "dataset_ref" | null;
  retry_policy: WorkflowRetryPolicy;
  timeout_ms: number;
}

export interface WorkflowEdgeDefinition {
  id: string;
  source: string;
  target: string;
  condition: string;
}

export interface WorkflowDefinition {
  name: string;
  nodes: WorkflowNodeDefinition[];
  edges: WorkflowEdgeDefinition[];
}

export interface WorkflowVersionRecord {
  id: string;
  workflow_id: string;
  version_number: number;
  created_at: string;
  created_by: string;
}

export interface WorkflowPlatformRecord {
  id: string;
  workspace_id: string;
  name: string;
  status: string;
  draft_snapshot: WorkflowDefinition;
  published_version_id: string | null;
  created_at: string;
  updated_at: string;
  created_by: string;
  updated_by: string;
  is_locked?: boolean;
  active_run_id?: string | null;
  active_run_status?: string | null;
  versions: WorkflowVersionRecord[];
  latest_version?: number | null;
  run_count?: number;
}

export interface WorkflowRunModeRequest {
  mode: "manual" | "trigger" | "test";
  debug?: boolean;
  input?: Record<string, unknown>;
  version_id?: string | null;
}

export interface WorkflowRunStep {
  id: string;
  run_id: string;
  node_id: string;
  node_type: string;
  status: string;
  attempt: number;
  input_snapshot: Record<string, unknown>;
  output_snapshot: Record<string, unknown> | null;
  decision_snapshot: Record<string, unknown> | null;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
}

export interface WorkflowRunRecord {
  id: string;
  workflow_id: string;
  workflow_version_id: string | null;
  workspace_id: string;
  mode: string;
  debug: number;
  parent_run_id: string | null;
  status: string;
  input_payload?: Record<string, unknown>;
  initial_input: Record<string, unknown>;
  context_snapshot: Record<string, unknown>;
  final_output: Record<string, unknown> | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  steps?: WorkflowRunStep[];
}

export interface WorkflowNodeType {
  type: string;
  family: string;
  label: string;
  supports_ai_brain: boolean;
  supports_memory: boolean;
  default_config: Record<string, unknown>;
  config_schema?: Record<string, { type?: string; required?: boolean }>;
  required_fields?: string[];
  secrets_required?: string[];
}

export interface WorkflowRunLog {
  node_id: string;
  node_type: string;
  status: string;
  message: string;
  timestamp: string;
  attempt: number;
}

export interface WorkflowRunLogsResponse {
  run_id: string;
  workflow_id: string;
  status: string;
  input_payload: Record<string, unknown>;
  context_snapshot: Record<string, unknown>;
  final_output: Record<string, unknown> | null;
  logs: WorkflowRunLog[];
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  category: string;
  difficulty: string;
  description: string;
  integrations_required: string[];
  workflow_snapshot: WorkflowDefinition;
  source?: "system" | "custom";
  owner_user_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface WorkflowTemplateVersion {
  id: string;
  template_id: string;
  version_number: number;
  change_summary: string;
  created_at: string;
  created_by: string;
}

export interface WorkflowLimits {
  workspace_id: string;
  max_nodes: number;
  max_depth: number;
  max_execution_time_ms: number;
  max_retries_total: number;
  max_sub_workflow_depth: number;
}

export interface AutosaveDraft {
  id: string;
  entity_type: string;
  entity_id: string;
  snapshot: WorkflowDefinition;
  saved_at: string;
}

export interface GeneratedWorkflowResponse extends WorkflowDefinition {
  explanation?: string;
  missing_integrations?: string[];
  confidence?: number;
  needs_confirmation?: boolean;
  plan_confidence?: number;
  parse_confidence?: number;
}

export interface VersionComparisonResult {
  v1: { version_number: number; created_at: string };
  v2: { version_number: number; created_at: string };
  nodes_added: string[];
  nodes_removed: string[];
  nodes_unchanged: string[];
  v1_node_count: number;
  v2_node_count: number;
}

export interface ApprovalTask {
  id: string;
  workflow_id: string;
  run_id: string;
  node_id: string;
  workspace_id: string;
  message: string;
  status: string;
  payload_snapshot: Record<string, unknown>;
  decision: string | null;
  decided_by: string | null;
  created_at: string;
  decided_at: string | null;
}

export interface LlmUsageRecord {
  id: string;
  workspace_id: string;
  run_id: string | null;
  node_id: string | null;
  model: string;
  tokens_used: number;
  cost: number;
  created_at: string;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

export const apiRoutes = {
  overview: `${API_BASE_URL}/api/overview`,
  chat: `${API_BASE_URL}/api/chat`,
  integrations: `${API_BASE_URL}/api/integrations`,
  integrationStatus: `${API_BASE_URL}/api/integrations/status`,
  saveIntegrationApiKey: `${API_BASE_URL}/api/integrations/save-api-key`,
  createIntegrationSession: `${API_BASE_URL}/api/integrations/create-session`,
  connectApiKey: `${API_BASE_URL}/api/connect/api-key`,
  connectOAuth: `${API_BASE_URL}/api/connect/oauth`,
  detectEnv: `${API_BASE_URL}/api/connect/env-detect`,
  knowledgeBaseDatasets: `${API_BASE_URL}/api/knowledge-base/datasets`,
  knowledgeBaseQuery: `${API_BASE_URL}/api/knowledge-base/query`,
  knowledgeBaseSeed: `${API_BASE_URL}/api/knowledge-base/seed`,
  workflowPlatform: `${API_BASE_URL}/api/workflows/platform`,
  workflowNodeTypes: `${API_BASE_URL}/api/node-types`,
  workflowTemplates: `${API_BASE_URL}/api/templates`,
  workflowApprovals: `${API_BASE_URL}/api/approvals`,
  workflowUsage: `${API_BASE_URL}/api/usage/llm`,
  workflowGenerate: `${API_BASE_URL}/api/generate-workflow`,
  workflowLimits: `${API_BASE_URL}/api/workflow-limits`,
  workflowAutosave: `${API_BASE_URL}/api/autosave`,
};

export async function getOverview(): Promise<OverviewData> {
  const response = await fetch(apiRoutes.overview);

  if (!response.ok) {
    throw new Error("Failed to load overview data from the backend.");
  }

  return (await response.json()) as OverviewData;
}

async function postJson<TResponse>(
  url: string,
  body: Record<string, unknown>,
): Promise<TResponse> {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(errorBody?.detail ?? "Request failed.");
  }

  return (await response.json()) as TResponse;
}

async function postJsonWithFallback<TResponse>(
  urls: string[],
  body: Record<string, unknown>,
): Promise<TResponse> {
  let lastError: Error | null = null;

  for (const url of urls) {
    try {
      return await postJson<TResponse>(url, body);
    } catch (error) {
      if (
        error instanceof Error &&
        (error.message === "Request failed." || error.message === "Not Found")
      ) {
        lastError = error;
        continue;
      }
      throw error;
    }
  }

  throw lastError ?? new Error("Request failed.");
}

export async function getIntegrations(): Promise<IntegrationsResponse> {
  const response = await fetch(apiRoutes.integrations);

  if (!response.ok) {
    throw new Error("Failed to load integrations.");
  }

  return (await response.json()) as IntegrationsResponse;
}

export async function getIntegrationStatus(
  provider: string,
): Promise<IntegrationStatusResponse> {
  const response = await fetch(
    `${apiRoutes.integrationStatus}?provider=${encodeURIComponent(provider)}`,
  );

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(errorBody?.detail ?? "Failed to load integration status.");
  }

  return (await response.json()) as IntegrationStatusResponse;
}

export async function detectIntegrationEnv(
  provider: string,
): Promise<EnvDetectResponse> {
  return postJson<EnvDetectResponse>(apiRoutes.detectEnv, { provider });
}

export async function connectIntegrationApiKey(
  provider: string,
  apiKey: string,
): Promise<ApiKeyConnectResponse> {
  return postJsonWithFallback<ApiKeyConnectResponse>(
    [apiRoutes.saveIntegrationApiKey, apiRoutes.connectApiKey],
    {
      provider,
      api_key: apiKey,
      user_id: "demo-user",
    },
  );
}

export async function createIntegrationSession(
  provider: string,
): Promise<OAuthSessionResponse> {
  return postJsonWithFallback<OAuthSessionResponse>(
    [apiRoutes.createIntegrationSession, apiRoutes.connectOAuth],
    {
      provider,
      user_id: "demo-user",
    },
  );
}

export async function disconnectIntegration(
  provider: string,
): Promise<{ provider: string; disconnected: boolean }> {
  const response = await fetch(
    `${apiRoutes.integrations}/${encodeURIComponent(provider)}`,
    {
      method: "DELETE",
    },
  );
  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(errorBody?.detail ?? "Disconnect failed.");
  }
  return (await response.json()) as { provider: string; disconnected: boolean };
}

export async function getKnowledgeBaseDatasets(): Promise<KnowledgeBaseDatasetsResponse> {
  const response = await fetch(apiRoutes.knowledgeBaseDatasets);

  if (!response.ok) {
    throw new Error("Failed to load datasets.");
  }

  return (await response.json()) as KnowledgeBaseDatasetsResponse;
}

export async function getKnowledgeBaseDocuments(
  datasetId: string,
  page = 1,
  limit = 10,
): Promise<KnowledgeBaseDocumentPage> {
  const response = await fetch(
    `${apiRoutes.knowledgeBaseDatasets}/${datasetId}/documents?page=${page}&limit=${limit}`,
  );

  if (!response.ok) {
    throw new Error("Failed to load dataset documents.");
  }

  return (await response.json()) as KnowledgeBaseDocumentPage;
}

export function getKnowledgeBaseFileUrl(datasetId: string, documentId: string): string {
  return `${apiRoutes.knowledgeBaseDatasets}/${datasetId}/documents/${documentId}/file`;
}

export async function uploadKnowledgeBaseDocument(
  datasetId: string,
  file: File,
): Promise<KnowledgeBaseUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `${apiRoutes.knowledgeBaseDatasets}/${datasetId}/upload`,
    {
      method: "POST",
      body: formData,
    },
  );

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(errorBody?.detail ?? "Upload failed.");
  }

  return (await response.json()) as KnowledgeBaseUploadResponse;
}

export async function deleteKnowledgeBaseDocument(
  datasetId: string,
  documentId: string,
): Promise<KnowledgeBaseDeleteResponse> {
  const response = await fetch(
    `${apiRoutes.knowledgeBaseDatasets}/${datasetId}/documents/${documentId}`,
    {
      method: "DELETE",
    },
  );

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(errorBody?.detail ?? "Delete failed.");
  }

  return (await response.json()) as KnowledgeBaseDeleteResponse;
}

export async function queryKnowledgeBase(
  datasetId: string,
  query: string,
  topK = 5,
): Promise<KnowledgeBaseQueryResponse> {
  return postJson<KnowledgeBaseQueryResponse>(apiRoutes.knowledgeBaseQuery, {
    dataset_id: datasetId,
    query,
    top_k: topK,
  });
}

export async function seedKnowledgeBase(): Promise<KnowledgeBaseSeedResponse> {
  return postJson<KnowledgeBaseSeedResponse>(apiRoutes.knowledgeBaseSeed, {});
}

export async function listPlatformWorkflows(): Promise<WorkflowPlatformRecord[]> {
  const response = await fetch(apiRoutes.workflowPlatform);
  if (!response.ok) {
    throw new Error("Failed to load workflows.");
  }
  return (await response.json()) as WorkflowPlatformRecord[];
}

export async function createPlatformWorkflow(
  name: string,
  snapshot: WorkflowDefinition,
): Promise<WorkflowPlatformRecord> {
  return postJson<WorkflowPlatformRecord>(apiRoutes.workflowPlatform, {
    name,
    snapshot,
  });
}

export async function getPlatformWorkflow(
  workflowId: string,
): Promise<WorkflowPlatformRecord> {
  const response = await fetch(`${apiRoutes.workflowPlatform}/${workflowId}`);
  if (!response.ok) {
    throw new Error("Failed to load workflow.");
  }
  return (await response.json()) as WorkflowPlatformRecord;
}

export async function updatePlatformWorkflow(
  workflowId: string,
  name: string,
  snapshot: WorkflowDefinition,
): Promise<WorkflowPlatformRecord> {
  return postJson<WorkflowPlatformRecord>(
    `${apiRoutes.workflowPlatform}/${workflowId}`,
    { name, snapshot },
  );
}

export async function validatePlatformWorkflow(
  workflowId: string,
  name: string,
  snapshot: WorkflowDefinition,
): Promise<{
  valid: boolean;
  nodes: number;
  edges: number;
  errors?: Array<{ node_id: string; message: string }>;
}> {
  return postJson(`${apiRoutes.workflowPlatform}/${workflowId}/validate`, {
    name,
    snapshot,
  });
}

export async function publishPlatformWorkflow(
  workflowId: string,
): Promise<WorkflowPlatformRecord> {
  return postJson<WorkflowPlatformRecord>(
    `${apiRoutes.workflowPlatform}/${workflowId}/publish`,
    {},
  );
}

export async function rollbackPlatformWorkflow(
  workflowId: string,
  versionId: string,
): Promise<WorkflowPlatformRecord> {
  return postJson<WorkflowPlatformRecord>(
    `${apiRoutes.workflowPlatform}/${workflowId}/rollback/${versionId}`,
    {},
  );
}

export async function runPlatformWorkflow(
  workflowId: string,
  request: WorkflowRunModeRequest,
): Promise<WorkflowRunRecord> {
  return postJson<WorkflowRunRecord>(
    `${apiRoutes.workflowPlatform}/${workflowId}/run`,
    request as unknown as Record<string, unknown>,
  );
}

export async function listPlatformRuns(
  workflowId: string,
): Promise<WorkflowRunRecord[]> {
  const response = await fetch(`${apiRoutes.workflowPlatform}/${workflowId}/runs`);
  if (!response.ok) {
    throw new Error("Failed to load workflow runs.");
  }
  return (await response.json()) as WorkflowRunRecord[];
}

export async function getPlatformRun(
  workflowId: string,
  runId: string,
): Promise<WorkflowRunRecord> {
  const response = await fetch(`${apiRoutes.workflowPlatform}/${workflowId}/runs/${runId}`);
  if (!response.ok) {
    throw new Error("Failed to load workflow run.");
  }
  return (await response.json()) as WorkflowRunRecord;
}

export async function getPlatformRunLogs(
  workflowId: string,
  runId: string,
): Promise<WorkflowRunLogsResponse | null> {
  const response = await fetch(
    `${apiRoutes.workflowPlatform}/${workflowId}/runs/${runId}/logs`,
  );
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error("Failed to load workflow logs.");
  }
  return (await response.json()) as WorkflowRunLogsResponse;
}

export async function listPlatformVersions(
  workflowId: string,
): Promise<WorkflowVersionRecord[]> {
  const response = await fetch(`${apiRoutes.workflowPlatform}/${workflowId}/versions`);
  if (!response.ok) {
    throw new Error("Failed to load versions.");
  }
  return (await response.json()) as WorkflowVersionRecord[];
}

export async function listWorkflowNodeTypes(): Promise<WorkflowNodeType[]> {
  const response = await fetch(apiRoutes.workflowNodeTypes);
  if (!response.ok) {
    throw new Error("Failed to load node types.");
  }
  return (await response.json()) as WorkflowNodeType[];
}

export async function listWorkflowTemplates(): Promise<WorkflowTemplate[]> {
  const response = await fetch(apiRoutes.workflowTemplates);
  if (!response.ok) {
    throw new Error("Failed to load templates.");
  }
  return (await response.json()) as WorkflowTemplate[];
}

export async function instantiateWorkflowTemplate(
  templateId: string,
): Promise<WorkflowPlatformRecord> {
  return postJson<WorkflowPlatformRecord>(
    `${apiRoutes.workflowTemplates}/${templateId}/instantiate`,
    {},
  );
}

export async function listWorkflowApprovals(): Promise<ApprovalTask[]> {
  const response = await fetch(apiRoutes.workflowApprovals);
  if (!response.ok) {
    throw new Error("Failed to load approvals.");
  }
  return (await response.json()) as ApprovalTask[];
}

export async function decideWorkflowApproval(
  approvalId: string,
  decision: "approve" | "reject",
): Promise<ApprovalTask> {
  return postJson<ApprovalTask>(
    `${apiRoutes.workflowApprovals}/${approvalId}/decision`,
    { decision },
  );
}

export async function listWorkflowUsage(): Promise<LlmUsageRecord[]> {
  const response = await fetch(apiRoutes.workflowUsage);
  if (!response.ok) {
    throw new Error("Failed to load LLM usage.");
  }
  return (await response.json()) as LlmUsageRecord[];
}

export async function generateWorkflowFromPrompt(
  prompt: string,
): Promise<GeneratedWorkflowResponse> {
  return postJson<GeneratedWorkflowResponse>(apiRoutes.workflowGenerate, { prompt });
}

// ── Template CRUD ─────────────────────────────────────────────────

export async function createWorkflowTemplate(
  name: string,
  category: string,
  difficulty: string,
  description: string,
  integrations: string[],
  snapshot: WorkflowDefinition,
): Promise<WorkflowTemplate> {
  return postJson<WorkflowTemplate>(apiRoutes.workflowTemplates, {
    name, category, difficulty, description,
    integrations_required: integrations, snapshot,
  });
}

export async function updateWorkflowTemplate(
  templateId: string,
  name: string,
  snapshot: WorkflowDefinition,
  changeSummary = "",
): Promise<WorkflowTemplate> {
  return postJson<WorkflowTemplate>(
    `${apiRoutes.workflowTemplates}/${templateId}`,
    { name, snapshot, change_summary: changeSummary },
  );
}

export async function deleteWorkflowTemplate(
  templateId: string,
): Promise<{ deleted: boolean }> {
  const response = await fetch(`${apiRoutes.workflowTemplates}/${templateId}`, { method: "DELETE" });
  if (!response.ok) {
    const err = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(err?.detail ?? "Delete failed.");
  }
  return (await response.json()) as { deleted: boolean };
}

export async function listTemplateVersions(
  templateId: string,
): Promise<WorkflowTemplateVersion[]> {
  const response = await fetch(`${apiRoutes.workflowTemplates}/${templateId}/versions`);
  if (!response.ok) throw new Error("Failed to load template versions.");
  return (await response.json()) as WorkflowTemplateVersion[];
}

export async function rollbackWorkflowTemplate(
  templateId: string,
  versionId: string,
): Promise<WorkflowTemplate> {
  return postJson<WorkflowTemplate>(
    `${apiRoutes.workflowTemplates}/${templateId}/rollback/${versionId}`, {},
  );
}

export async function compareTemplateVersions(
  templateId: string,
  v1Id: string,
  v2Id: string,
): Promise<VersionComparisonResult> {
  const response = await fetch(
    `${apiRoutes.workflowTemplates}/${templateId}/compare/${v1Id}/${v2Id}`,
  );
  if (!response.ok) throw new Error("Failed to compare versions.");
  return (await response.json()) as VersionComparisonResult;
}

// ── Workflow Limits ─────────────────────────────────────────────

export async function getWorkflowLimits(): Promise<WorkflowLimits> {
  const response = await fetch(apiRoutes.workflowLimits);
  if (!response.ok) throw new Error("Failed to load workflow limits.");
  return (await response.json()) as WorkflowLimits;
}

export async function updateWorkflowLimits(
  limits: Partial<WorkflowLimits>,
): Promise<WorkflowLimits> {
  return postJson<WorkflowLimits>(apiRoutes.workflowLimits, limits as Record<string, unknown>);
}

// ── Autosave ─────────────────────────────────────────────────────

export async function autosaveWorkflowDraft(
  entityType: string,
  entityId: string,
  snapshot: WorkflowDefinition,
): Promise<AutosaveDraft> {
  return postJson<AutosaveDraft>(apiRoutes.workflowAutosave, {
    entity_type: entityType, entity_id: entityId, snapshot,
  });
}

export async function getAutosaveDraft(
  entityType: string,
  entityId: string,
): Promise<AutosaveDraft | null> {
  const response = await fetch(`${apiRoutes.workflowAutosave}/${entityType}/${entityId}`);
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("Failed to load autosave draft.");
  return (await response.json()) as AutosaveDraft;
}
