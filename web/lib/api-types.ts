// Type-only definitions for the VidiForge API. Mirrors api/app/models/schema.py.
// Keep this in sync when adding new fields.

export type LLMProvider =
  | "openai"
  | "anthropic"
  | "deepseek"
  | "gemini"
  | "moonshot"
  | "qwen"
  | "openai_compatible";

export interface ApiKeyEntry {
  provider: string;
  masked: string;
  updated_at: string;
  has_value: boolean;
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