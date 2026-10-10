// @vidiforge/shared — TypeScript types mirroring Pydantic schemas.
// Keep this file in sync with api/app/models/schema.py.

export type LLMProvider =
  | "openai"
  | "anthropic"
  | "deepseek"
  | "gemini"
  | "moonshot"
  | "qwen"
  | "openai_compatible";

export type VoiceProvider = "edge" | "azure" | "elevenlabs" | "siliconflow";
export type SubtitleProvider = "edge" | "whisper";
export type MaterialProvider = "pexels" | "pixabay" | "upload";
export type AspectRatio = "9:16" | "16:9" | "1:1";
export type Language = "zh-CN" | "en-US" | "ja-JP";
export type TaskStatus = "pending" | "running" | "done" | "failed";

export interface ScriptSegment {
  id: number;
  text: string;
  keyword: string;
  duration: number;
}

export interface Script {
  title: string;
  segments: ScriptSegment[];
}

export interface VoiceConfig {
  provider: VoiceProvider;
  voice_id: string;
  speed: number;
  pitch: number;
}

export interface SubtitleConfig {
  provider: SubtitleProvider;
  font: string;
  font_size: number;
  font_color: string;
  position: "bottom" | "center" | "top";
  outline_color: string;
  outline_width: number;
}

export interface MaterialConfig {
  provider: MaterialProvider;
  orientation: "portrait" | "landscape" | "square";
}

export interface BGMConfig {
  enabled: boolean;
  volume: number;
  random: boolean;
  path: string | null;
}

export interface VideoRequest {
  topic: string;
  keywords: string[];
  language: Language;
  aspect: AspectRatio;
  duration: number;
  segments: number;
  llm_provider: LLMProvider;
  script: Script | null;
  voice: VoiceConfig;
  subtitle: SubtitleConfig;
  material: MaterialConfig;
  bgm: BGMConfig;
  api_keys: Record<string, string>;
}

export interface TaskStage {
  name: string;
  status: TaskStatus;
  progress: number;
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
}

export interface VideoTask {
  id: string;
  topic: string;
  aspect: AspectRatio;
  status: TaskStatus;
  progress: number;
  current_stage: string | null;
  script: Script | null;
  output_path: string | null;
  output_url: string | null;
  duration: number | null;
  file_size: number | null;
  stages: TaskStage[];
  error: string | null;
  config: VideoRequest | null;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  total: number;
  tasks: VideoTask[];
}

export interface ApiKeyEntry {
  provider: string;
  masked: string;
  updated_at: string;
  has_value: boolean;
}

export interface ApiKeySave {
  provider: string;
  value: string;
}

export interface LLMProviderInfo {
  id: LLMProvider;
  name: string;
  default_model: string;
  requires_key: boolean;
  available: boolean;
  active: boolean;
  env_key?: string;
  byok_key?: string;
}

export interface VoiceProviderInfo {
  id: VoiceProvider;
  name: string;
  requires_key: boolean;
  available: boolean;
  voices: { id: string; name: string; gender: string; language: string }[];
  active: boolean;
}

export interface HealthResponse {
  ok: boolean;
  version: string;
  env: string;
  ffmpeg: string;
}