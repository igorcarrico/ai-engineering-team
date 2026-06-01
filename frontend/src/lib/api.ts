// Typed API client. Uses same-origin /api (proxied to the backend by Next).

import type {
  ArtifactRead,
  ChatExchange,
  ChatMessage,
  CreateProjectRequest,
  ProjectRead,
  ProjectSummary,
  RunDetail,
  RunEvent,
  RuntimeConfig,
  SendMessageRequest,
  WorkspaceTree,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  config: () => request<RuntimeConfig>("/config"),

  createProject: (body: CreateProjectRequest) =>
    request<RunDetail>("/projects", { method: "POST", body: JSON.stringify(body) }),

  listProjects: () => request<ProjectSummary[]>("/projects"),

  getProject: (id: string) => request<ProjectRead>(`/projects/${id}`),

  rerunProject: (id: string) =>
    request<RunDetail>(`/projects/${id}/rerun`, { method: "POST" }),

  getRun: (id: string) => request<RunDetail>(`/runs/${id}`),

  getRunEvents: (id: string) => request<RunEvent[]>(`/runs/${id}/events`),

  listArtifacts: (runId: string) => request<ArtifactRead[]>(`/runs/${runId}/artifacts`),

  getTree: (runId: string) => request<WorkspaceTree>(`/runs/${runId}/tree`),

  getArtifact: (id: string) => request<ArtifactRead>(`/artifacts/${id}`),

  // Direct download URLs (used in <a href>).
  exportUrl: (runId: string, fmt: "md" | "json" | "zip") =>
    `${BASE}/runs/${runId}/export.${fmt}`,

  briefUrl: (runId: string) => `${BASE}/runs/${runId}/brief.html`,

  streamUrl: (runId: string) => `${BASE}/runs/${runId}/stream`,

  listChat: (runId: string) => request<ChatMessage[]>(`/runs/${runId}/chat`),

  sendChat: (runId: string, body: SendMessageRequest) =>
    request<ChatExchange>(`/runs/${runId}/chat`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

export { ApiError };
