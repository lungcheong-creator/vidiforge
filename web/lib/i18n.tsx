"use client";

import { createContext, useContext, useEffect, useState } from "react";

type Lang = "zh" | "en";

const dict: Record<string, { zh: string; en: string }> = {
  // brand
  brand: { zh: "VidiForge 智選銀河", en: "VidiForge" },

  // nav
  nav_dashboard: { zh: "工作台", en: "Dashboard" },
  nav_create: { zh: "創建視頻", en: "Create" },
  nav_workspace: { zh: "項目編輯", en: "Workspace" },
  nav_batch: { zh: "批量任務", en: "Batch Tasks" },
  nav_history: { zh: "歷史記錄", en: "History" },
  nav_agent: { zh: "AI 助手", en: "AI Agent" },
  nav_settings: { zh: "設置", en: "Settings" },

  // dashboard
  dash_greeting_morning: { zh: "早上好", en: "Good morning" },
  dash_greeting_afternoon: { zh: "下午好", en: "Good afternoon" },
  dash_greeting_evening: { zh: "晚上好", en: "Good evening" },
  dash_subtitle: { zh: "從一個想法到一段成片，VidiForge 為你加速。", en: "From an idea to a finished reel — VidiForge accelerates your craft." },
  dash_quick_start: { zh: "快速開始", en: "Quick Start" },
  dash_quick_start_desc: { zh: "輸入主題，讓 AI 為你生成完整短視頻。", en: "Enter a topic, let AI generate a complete short video for you." },
  dash_input_placeholder: { zh: "例如：北歐風家居擺設的 5 個技巧", en: "e.g. 5 styling tips for Nordic home decor" },
  dash_generate: { zh: "開始生成", en: "Generate" },
  dash_stats_videos: { zh: "本月成片", en: "Videos this month" },
  dash_stats_minutes: { zh: "生成分鐘", en: "Minutes rendered" },
  dash_stats_calls: { zh: "API 調用", en: "API calls" },
  dash_recent: { zh: "最近項目", en: "Recent Projects" },
  dash_recent_all: { zh: "查看全部", en: "View all" },
  dash_services: { zh: "服務健康", en: "Service Status" },
  dash_connected: { zh: "已連接", en: "Connected" },
  dash_missing: { zh: "未配置", en: "Missing key" },
  dash_active: { zh: "活躍", en: "Active" },

  // create
  create_title: { zh: "創建新視頻", en: "Create New Video" },
  create_subtitle: { zh: "選擇畫幅、配置參數，AI 將自動完成腳本 → 配音 → 素材 → 字幕 → 渲染。", en: "Pick a format, configure options — AI handles script → voice → footage → subtitles → render." },
  create_step_topic: { zh: "主題", en: "Topic" },
  create_step_script: { zh: "腳本", en: "Script" },
  create_step_material: { zh: "素材", en: "Footage" },
  create_step_voice: { zh: "配音", en: "Voice" },
  create_step_subtitle: { zh: "字幕", en: "Subtitle" },
  create_step_render: { zh: "合成", en: "Render" },
  create_aspect: { zh: "畫幅比例", en: "Aspect Ratio" },
  create_aspect_vertical: { zh: "豎屏 9:16", en: "Vertical 9:16" },
  create_aspect_horizontal: { zh: "橫屏 16:9", en: "Horizontal 16:9" },
  create_aspect_square: { zh: "方形 1:1", en: "Square 1:1" },
  create_duration: { zh: "視頻時長", en: "Duration" },
  create_segments: { zh: "段落數", en: "Segments" },
  create_material_source: { zh: "素材來源", en: "Material Source" },
  create_material_pexels: { zh: "Pexels 線上素材", en: "Pexels online" },
  create_material_pixabay: { zh: "Pixabay 線上素材", en: "Pixabay online" },
  create_material_ai: { zh: "AI 文生視頻", en: "AI text-to-video" },
  create_material_upload: { zh: "本地上傳", en: "Local upload" },
  create_language: { zh: "腳本語言", en: "Script Language" },
  create_voice_provider: { zh: "配音服務", en: "Voice Provider" },
  create_bg_music: { zh: "背景音樂", en: "Background Music" },
  create_start: { zh: "開始生成", en: "Start Generating" },

  // workspace
  ws_title: { zh: "項目編輯", en: "Project Workspace" },
  ws_project: { zh: "北歐家居 5 個技巧", en: "Nordic Home — 5 Styling Tips" },
  ws_save: { zh: "保存", en: "Save" },
  ws_render: { zh: "一鍵渲染", en: "Render" },
  ws_script_preview: { zh: "腳本預覽", en: "Script Preview" },
  ws_segments: { zh: "段落", en: "Segments" },
  ws_voice: { zh: "配音", en: "Voice" },
  ws_subtitle_style: { zh: "字幕樣式", en: "Subtitle Style" },
  ws_footage: { zh: "素材庫", en: "Footage Library" },

  // batch
  batch_title: { zh: "批量任務", en: "Batch Tasks" },
  batch_new: { zh: "新建批量", en: "New Batch" },
  batch_import: { zh: "導入 JSON", en: "Import JSON" },
  batch_status_queued: { zh: "排隊中", en: "Queued" },
  batch_status_running: { zh: "渲染中", en: "Rendering" },
  batch_status_done: { zh: "已完成", en: "Completed" },
  batch_status_failed: { zh: "失敗", en: "Failed" },

  // history
  hist_title: { zh: "歷史記錄", en: "History" },
  hist_filter_all: { zh: "全部", en: "All" },
  hist_filter_done: { zh: "已完成", en: "Completed" },
  hist_filter_failed: { zh: "失敗", en: "Failed" },
  hist_filter_draft: { zh: "草稿", en: "Drafts" },
  hist_download: { zh: "下載", en: "Download" },
  hist_preview: { zh: "預覽", en: "Preview" },

  // agent
  agent_title: { zh: "AI 助手", en: "AI Agent" },
  agent_subtitle: { zh: "用對話驅動整個創作流程。", en: "Drive the whole creation flow through conversation." },
  agent_placeholder: { zh: "告訴助手你想做什麼…", en: "Tell the agent what you want to create…" },
  agent_send: { zh: "發送", en: "Send" },
  agent_quick_1: { zh: "做一個 30 秒關於早晨習慣的短視頻", en: "Make a 30s reel about morning routines" },
  agent_quick_2: { zh: "幫我把這 5 個片段合併成一個 60 秒的成片", en: "Merge these 5 clips into a 60s final video" },
  agent_quick_3: { zh: "把這段英文腳本翻譯成日文並重新配音", en: "Translate this English script to Japanese and re-voice it" },

  // settings
  set_title: { zh: "設置", en: "Settings" },
  set_tab_keys: { zh: "API 密鑰", en: "API Keys" },
  set_tab_prefs: { zh: "偏好", en: "Preferences" },
  set_tab_storage: { zh: "存儲", en: "Storage" },
  set_tab_about: { zh: "關於", en: "About" },
  set_keys_desc: { zh: "密鑰使用 AES-256 加密保存於本地，未上傳任何服務器。", en: "Keys are encrypted with AES-256 locally; never uploaded to any server." },
  set_unlock: { zh: "解鎖", en: "Unlock" },
  set_locked: { zh: "已鎖定", en: "Locked" },
  set_storage_used: { zh: "已使用", en: "Used" },
  set_storage_total: { zh: "總配額", en: "Total quota" },
  set_storage_local: { zh: "本地存儲", en: "Local storage" },
  set_storage_cloud: { zh: "雲端備份", en: "Cloud backup" },

  // common
  common_yes: { zh: "是", en: "Yes" },
  common_no: { zh: "否", en: "No" },
  common_save: { zh: "保存", en: "Save" },
  common_cancel: { zh: "取消", en: "Cancel" },
  common_continue: { zh: "繼續", en: "Continue" },
  common_back: { zh: "返回", en: "Back" },
  common_delete: { zh: "刪除", en: "Delete" },
  common_edit: { zh: "編輯", en: "Edit" },
};

type Ctx = {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;
};
const LangCtx = createContext<Ctx>({ lang: "zh", setLang: () => {}, t: (k) => dict[k]?.zh ?? k });

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("zh");

  useEffect(() => {
    const saved = (typeof window !== "undefined" && localStorage.getItem("vf_lang")) as Lang | null;
    if (saved === "zh" || saved === "en") setLangState(saved);
  }, []);

  const setLang = (l: Lang) => {
    setLangState(l);
    if (typeof window !== "undefined") localStorage.setItem("vf_lang", l);
  };

  const t = (key: string) => dict[key]?.[lang] ?? dict[key]?.en ?? key;

  return <LangCtx.Provider value={{ lang, setLang, t }}>{children}</LangCtx.Provider>;
}

export function useLang() {
  return useContext(LangCtx);
}