// Types mirroring the backend API DTOs.

export type RunStatus = "pending" | "running" | "completed" | "failed" | "cancelled";
export type StepStatus = "pending" | "running" | "completed" | "failed" | "skipped";

export type AgentKey =
  | "product_manager"
  | "architect"
  | "backend_engineer"
  | "frontend_engineer"
  | "qa_engineer"
  | "security_reviewer"
  | "code_reviewer"
  | "supervisor";

export type EventType =
  | "run_started"
  | "agent_started"
  | "agent_progress"
  | "agent_completed"
  | "agent_failed"
  | "agent_retry"
  | "artifact_created"
  | "routing_decision"
  | "iteration_started"
  | "run_completed"
  | "run_failed";

export interface RunEvent {
  id: string;
  seq?: number;
  run_id: string;
  type: EventType;
  agent: AgentKey | null;
  agent_label: string | null;
  message: string;
  iteration: number;
  data: Record<string, unknown>;
  created_at: string;
}

export interface StepRead {
  agent: AgentKey;
  label: string;
  status: StepStatus;
  iteration: number;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  retries: number;
  error: string | null;
}

export interface RunRead {
  id: string;
  project_id: string;
  status: RunStatus;
  provider: string;
  model: string;
  iteration: number;
  max_iterations: number;
  created_at: string;
  updated_at: string;
  duration_ms: number | null;
  steps: StepRead[];
  review_score: number | null;
  final_summary: string | null;
}

export interface ProjectRead {
  id: string;
  name: string;
  idea: string;
  constraints: string;
  created_at: string;
  updated_at: string;
  latest_run: RunRead | null;
}

export interface ProjectSummary {
  id: string;
  name: string;
  idea: string;
  created_at: string;
  latest_run_id: string | null;
  latest_status: RunStatus | null;
  review_score: number | null;
  artifact_count: number;
}

export interface RunDetail {
  run: RunRead;
  project: ProjectRead;
  outputs: Record<string, any>;
  events: RunEvent[];
  artifact_count: number;
}

export type ArtifactKind = "document" | "code" | "diagram" | "plan" | "report";

export interface ArtifactRead {
  id: string;
  run_id: string;
  title: string;
  path: string;
  kind: ArtifactKind;
  language: string;
  produced_by: AgentKey;
  content: string;
  summary: string;
  created_at: string;
}

export interface ArtifactTreeNode {
  name: string;
  path: string;
  is_dir: boolean;
  kind: ArtifactKind | null;
  artifact_id: string | null;
  children: ArtifactTreeNode[];
}

export interface WorkspaceTree {
  root: ArtifactTreeNode;
  total_files: number;
  by_kind: Record<string, number>;
}

export interface CreateProjectRequest {
  idea: string;
  name?: string;
  constraints?: string;
  provider?: string;
  model?: string;
  max_iterations?: number;
}

export interface RuntimeConfig {
  version: string;
  default_provider: string;
  providers: string[];
  models: Record<string, string>;
  max_iterations: number;
  agents: AgentKey[];
}
