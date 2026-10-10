/** Typed fetch client for the VidiForge API. */
import type {
  ApiKeyEntry,
  ApiKeySave,
  HealthResponse,
  TaskListResponse,
  VideoRequest,
  VideoTask,
  LLMProviderInfo,
  VoiceProviderInfo,
} from "@vidiforge/shared";

// When deployed as static export served by FastAPI, all requests go to same origin.
// In dev mode, override with NEXT_PUBLIC_API_URL (e.g. http://localhost:8080).
const BASE_URL =
  (typeof window !== "undefined" && (window as any).__VIDIFORGE_API_URL__) ||
  process.env.NEXT_PUBLIC_API_URL ||
  "";

const TOKEN_STORAGE_KEY = "vf_api_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setToken(token: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers || {});
  headers.set("Accept", "application/json");
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const url = `${BASE_URL.replace(/\/$/, "")}${path}`;
  const res = await fetch(url, { ...init, headers });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      msg = data.detail || data.message || msg;
    } catch {}
    throw new Error(msg);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ============ Health ============
export const getHealth = () => request<HealthResponse>("/healthz");

// ============ Videos ============
export const createVideo = (req: VideoRequest | Record<string, any>) =>
  request<VideoTask>("/api/v1/videos", {
    method: "POST",
    body: JSON.stringify(req),
  });

export const getTask = (id: string) => request<VideoTask>(`/api/v1/tasks/${id}`);

export const listTasks = (limit = 50, offset = 0) =>
  request<TaskListResponse>(`/api/v1/tasks?limit=${limit}&offset=${offset}`);

export const deleteTask = (id: string) =>
  request<{ ok: boolean; task_id: string }>(`/api/v1/tasks/${id}`, { method: "DELETE" });

// ============ Providers ============
export const listLLMProviders = () =>
  request<LLMProviderInfo[]>("/api/v1/llm/providers");

export const listVoiceProviders = () =>
  request<VoiceProviderInfo[]>("/api/v1/voice/providers");

export const listMaterialProviders = () =>
  request<{ id: string; name: string; available: boolean; active: boolean }[]>(
    "/api/v1/materials/providers"
  );

// ============ Settings / API Keys ============
export const listKeys = () => request<ApiKeyEntry[]>("/api/v1/settings/keys");

export const saveKey = (provider: string, value: string) =>
  request<ApiKeyEntry>("/api/v1/settings/keys", {
    method: "POST",
    body: JSON.stringify({ provider, value } as ApiKeySave),
  });

export const deleteKey = (provider: string) =>
  request<{ ok: boolean; provider: string }>(
    `/api/v1/settings/keys/${provider}`,
    { method: "DELETE" }
  );

// ============ Stream/Download helpers ============
export function streamUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  const token = getToken();
  const base = BASE_URL.replace(/\/$/, "");
  return token
    ? `${base}/api/v1/stream/${path}?token=${encodeURIComponent(token)}`
    : `${base}/api/v1/stream/${path}`;
}

export function downloadUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  const token = getToken();
  const base = BASE_URL.replace(/\/$/, "");
  return token
    ? `${base}/api/v1/download/${path}?token=${encodeURIComponent(token)}`
    : `${base}/api/v1/download/${path}`;
}

/** Download URL for a finished task; the API redirects to a signed GCS URL. */
export function taskFileUrl(taskId: string): string {
  const token = getToken();
  const base = BASE_URL.replace(/\/$/, "");
  return `${base}/api/v1/tasks/${taskId}/file${
    token ? `?token=${encodeURIComponent(token)}` : ""
  }`;
}

// ============ Batches ============
export interface BatchSummary {
  id: string;
  name: string;
  status: "pending" | "running" | "done" | "failed";
  total: number;
  completed: number;
  failed: number;
  topics: string[];
  task_ids: string[];
  created_at: string;
  updated_at: string;
  error: string | null;
  tasks?: {
    id: string;
    topic: string;
    status: string;
    progress: number;
    current_stage: string | null;
    error: string | null;
    duration: number | null;
  }[];
}

export const createBatch = (body: {
  name: string;
  topics: string[];
  duration?: number;
  segments?: number;
  aspect?: "9:16" | "16:9" | "1:1";
  llm_model?: string;
}) =>
  request<BatchSummary>("/api/v1/batches", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const listBatches = (limit = 50, offset = 0) =>
  request<{ total: number; batches: BatchSummary[] }>(
    `/api/v1/batches?limit=${limit}&offset=${offset}`
  );

export const getBatch = (id: string) => request<BatchSummary>(`/api/v1/batches/${id}`);

export const deleteBatch = (id: string) =>
  request<{ ok: boolean; batch_id: string }>(`/api/v1/batches/${id}`, { method: "DELETE" });

// ============ Agent ============
export interface AgentToolCall {
  tool: string;
  arguments: Record<string, unknown>;
  result: Record<string, unknown>;
}

export interface AgentReply {
  reply: string;
  model: string;
  tool_calls: AgentToolCall[];
}

export const agentChat = (messages: { role: "user" | "assistant"; content: string }[], model = "deepseek-flash") =>
  request<AgentReply>("/api/v1/agent/chat", {
    method: "POST",
    body: JSON.stringify({ messages, model }),
  });

export const listAgentTools = () =>
  request<{ name: string; description: string }[]>("/api/v1/agent/tools");

// ============ Models catalogue ============
export const listModels = () =>
  request<{ provider: string; id: string; name: string; note: string }[]>(
    "/api/v1/llm/models"
  );

// Note: stream/download URLs carry the token in the query string because
// <video> and <a download> cannot set an Authorization header.
