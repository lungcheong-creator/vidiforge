"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useLang } from "@/lib/i18n";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea, Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Wand2, ArrowRight, ArrowLeft, Check, Mic, Type, Music,
  ImageIcon, Sparkles, AlertCircle, Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { createVideo } from "@/lib/api";

const STEPS = [
  { key: "create_step_topic", label: "Subject", num: "I" },
  { key: "create_step_script", label: "Script", num: "II" },
  { key: "create_step_material", label: "Footage", num: "III" },
  { key: "create_step_voice", label: "Voice", num: "IV" },
  { key: "create_step_subtitle", label: "Subtitle", num: "V" },
  { key: "create_step_render", label: "Render", num: "VI" },
];

export default function CreatePage() {
  const { t, lang } = useLang();
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [topic, setTopic] = useState(lang === "zh"
    ? "北歐風家居擺設的 5 個技巧，適合 25-35 歲年輕人。"
    : "5 styling tips for Nordic home decor");
  const [keywords, setKeywords] = useState("");
  const [aspect, setAspect] = useState("9:16");
  const [duration, setDuration] = useState(30);
  const [segments, setSegments] = useState(5);
  const [materialSrc, setMaterialSrc] = useState("pexels");
  const [voiceProvider, setVoiceProvider] = useState("edge");
  const [voiceId, setVoiceId] = useState("zh-CN-XiaoxiaoNeural");
  const [subtitlePosition, setSubtitlePosition] = useState("bottom");
  const [subtitleFontSize, setSubtitleFontSize] = useState(48);
  const [bgmEnabled, setBgmEnabled] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  async function handleStart() {
    setSubmitting(true);
    setError(null);
    try {
      const req = {
        topic,
        keywords: keywords.split(/[,，]/).map(k => k.trim()).filter(Boolean),
        language: "zh-CN",
        aspect,
        duration,
        segments,
        llm_provider: "openai",
        script: null,
        voice: { provider: voiceProvider, voice_id: voiceId, speed: 1.0, pitch: 0.0 },
        subtitle: {
          provider: "edge",
          font: "Noto Sans CJK SC",
          font_size: subtitleFontSize,
          font_color: "#FFFFFF",
          position: subtitlePosition,
          outline_color: "#000000",
          outline_width: 2,
        },
        material: {
          provider: materialSrc,
          orientation: aspect === "9:16" ? "portrait" : aspect === "16:9" ? "landscape" : "square",
        },
        bgm: { enabled: bgmEnabled, volume: 0.3, random: true, path: null },
        api_keys: {},
      };

      const task = await createVideo(req);
      router.push(`/workspace?task_id=${task.id}`);
    } catch (e) {
      setError(e && e.message ? e.message : "Failed to create video");
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 space-y-10">
      <header className="grid gap-6 lg:grid-cols-[1fr_auto] lg:items-end">
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-xs uppercase tracking-widest text-muted-foreground">
            <span>No.</span>
            <span>002</span>
            <span>Create · {STEPS[step].label}</span>
          </div>
          <h1 className="font-display text-5xl font-medium tracking-tight">
            {lang === "zh" ? "一個新的" : "A New"}
            <span className="italic text-primary"> {lang === "zh" ? "故事" : "Story"}.</span>
          </h1>
        </div>
        <div>
          <span className="text-6xl font-medium tabular-nums text-primary">{String(step + 1).padStart(2, "0")}</span>
          <span className="text-2xl italic text-muted-foreground"> / {String(STEPS.length).padStart(2, "0")}</span>
        </div>
      </header>

      {error && (
        <div className="flex items-start gap-3 rounded-sm border border-destructive/40 bg-destructive/5 p-4">
          <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="text-sm font-medium">{lang === "zh" ? "創建失敗" : "Failed to create"}</div>
            <div className="text-xs text-muted-foreground mt-1">{error}</div>
          </div>
        </div>
      )}

      <Card className="p-8 space-y-6">
        <div className="flex items-baseline justify-between">
          <h2 className="text-2xl font-medium">{STEPS[step].label}</h2>
        </div>

        {step === 0 && (
          <div className="space-y-4">
            <label className="text-xs font-medium text-muted-foreground block">
              {lang === "zh" ? "視頻主題" : "Subject"}
            </label>
            <Textarea
              rows={4}
              placeholder={lang === "zh" ? "北歐家居..." : "Nordic decor..."}
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
            <label className="text-xs font-medium text-muted-foreground block">
              {lang === "zh" ? "關鍵詞" : "Keywords"}
            </label>
            <Input
              placeholder={lang === "zh" ? "北歐, 簡約" : "nordic, minimalist"}
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
            />
          </div>
        )}

        {step === 1 && (
          <p className="text-sm italic text-muted-foreground">
            {lang === "zh" ? "點擊「開始生成」後 AI 將為你撰寫腳本。" : "AI will write the script on submit."}
          </p>
        )}

        {step === 2 && (
          <div className="space-y-3">
            <label className="text-xs font-medium text-muted-foreground block">
              {lang === "zh" ? "素材來源" : "Footage source"}
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { k: "pexels", l: "Pexels" },
                { k: "pixabay", l: "Pixabay" },
                { k: "upload", l: lang === "zh" ? "上傳" : "Upload" },
              ].map((o) => (
                <button
                  key={o.k}
                  onClick={() => setMaterialSrc(o.k)}
                  className={cn(
                    "rounded-md border p-3 text-sm",
                    materialSrc === o.k ? "border-primary bg-primary/10" : "border-border"
                  )}
                >
                  {o.l}
                </button>
              ))}
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-3">
            <label className="text-xs font-medium text-muted-foreground block">
              {lang === "zh" ? "配音服務" : "Voice provider"}
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { k: "edge", l: "Edge TTS" },
                { k: "azure", l: "Azure" },
                { k: "elevenlabs", l: "ElevenLabs" },
              ].map((o) => (
                <button
                  key={o.k}
                  onClick={() => setVoiceProvider(o.k)}
                  className={cn(
                    "rounded-md border p-3 text-sm",
                    voiceProvider === o.k ? "border-primary bg-primary/10" : "border-border"
                  )}
                >
                  {o.l}
                </button>
              ))}
            </div>
            <label className="text-xs font-medium text-muted-foreground block mt-3">
              {lang === "zh" ? "音色" : "Voice"}
            </label>
            <select
              value={voiceId}
              onChange={(e) => setVoiceId(e.target.value)}
              className="w-full h-10 rounded-md border bg-background px-3 text-sm"
            >
              <option value="zh-CN-XiaoxiaoNeural">曉曉 (zh-CN)</option>
              <option value="zh-CN-YunxiNeural">雲希 (zh-CN)</option>
              <option value="en-US-AriaNeural">Aria (en-US)</option>
            </select>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-3">
            <label className="text-xs font-medium text-muted-foreground block">
              {lang === "zh" ? "字幕位置" : "Position"}
            </label>
            <select
              value={subtitlePosition}
              onChange={(e) => setSubtitlePosition(e.target.value)}
              className="w-full h-10 rounded-md border bg-background px-3 text-sm"
            >
              <option value="bottom">{lang === "zh" ? "底部" : "Bottom"}</option>
              <option value="center">{lang === "zh" ? "居中" : "Center"}</option>
              <option value="top">{lang === "zh" ? "頂部" : "Top"}</option>
            </select>
            <label className="text-xs font-medium text-muted-foreground block mt-3">
              {lang === "zh" ? "大小" : "Size"}
            </label>
            <Input
              type="number"
              value={String(subtitleFontSize)}
              onChange={(e) => setSubtitleFontSize(Number(e.target.value))}
            />
          </div>
        )}

        {step === 5 && (
          <div className="space-y-4">
            <label className="text-xs font-medium text-muted-foreground block">
              {lang === "zh" ? "畫幅" : "Aspect"}
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { k: "9:16", l: "Vertical" },
                { k: "16:9", l: "Horizontal" },
                { k: "1:1", l: "Square" },
              ].map((o) => (
                <button
                  key={o.k}
                  onClick={() => setAspect(o.k)}
                  className={cn(
                    "rounded-md border p-3 text-sm",
                    aspect === o.k ? "border-primary bg-primary/10" : "border-border"
                  )}
                >
                  {o.l}
                </button>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground block">
                  {lang === "zh" ? "時長" : "Duration"}
                </label>
                <Input
                  type="number"
                  value={String(duration)}
                  onChange={(e) => setDuration(Number(e.target.value))}
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground block">
                  {lang === "zh" ? "段落" : "Segments"}
                </label>
                <Input
                  type="number"
                  value={String(segments)}
                  onChange={(e) => setSegments(Number(e.target.value))}
                />
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setBgmEnabled(!bgmEnabled)}
                className={cn(
                  "h-6 w-11 rounded-full relative transition-colors",
                  bgmEnabled ? "bg-primary" : "bg-muted"
                )}
              >
                <div
                  className={cn(
                    "absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all shadow",
                    bgmEnabled ? "left-5" : "left-0.5"
                  )}
                />
              </button>
              <span className="text-sm">BGM {bgmEnabled ? (lang === "zh" ? "開啟" : "On") : (lang === "zh" ? "關閉" : "Off")}</span>
            </div>
          </div>
        )}
      </Card>

      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          onClick={() => setStep(Math.max(0, step - 1))}
          disabled={step === 0 || submitting}
        >
          <ArrowLeft className="h-4 w-4 mr-1" /> {lang === "zh" ? "返回" : "Back"}
        </Button>
        <div className="text-xs text-muted-foreground tabular-nums">
          Step {step + 1} / {STEPS.length}
        </div>
        {step < STEPS.length - 1 ? (
          <Button onClick={() => setStep(step + 1)}>
            {lang === "zh" ? "繼續" : "Continue"} <ArrowRight className="h-4 w-4 ml-1" />
          </Button>
        ) : (
          <Button
            onClick={handleStart}
            disabled={submitting || !topic.trim()}
            className="bg-primary text-primary-foreground"
          >
            {submitting ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Wand2 className="h-4 w-4 mr-1" />}
            {submitting
              ? (lang === "zh" ? "提交中…" : "Submitting…")
              : (lang === "zh" ? "開始生成" : "Generate")}
          </Button>
        )}
      </div>
    </div>
  );
}