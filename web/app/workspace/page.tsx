"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useLang } from "@/lib/i18n";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Play, Volume2, Wand2, Save, Download, AlertCircle, Loader2, ArrowLeft, Film, Mic, Type, Music, ImageIcon } from "lucide-react";
import { getTask, streamUrl, downloadUrl } from "@/lib/api";
import type { VideoTask } from "@vidiforge/shared";

const STAGES = [
  { name: "script", zh: "腳本", num: "I" },
  { name: "voice", zh: "配音", num: "II" },
  { name: "footage", zh: "素材", num: "III" },
  { name: "subtitle", zh: "字幕", num: "IV" },
  { name: "bgm", zh: "BGM", num: "V" },
  { name: "render", zh: "渲染", num: "VI" },
];

function WorkspaceInner() {
  const params = useSearchParams();
  const router = useRouter();
  const taskId = params.get("task_id");
  const { t, lang } = useLang();

  const [task, setTask] = useState<VideoTask | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!taskId) return;
    let cancelled = false;

    async function poll() {
      try {
        const t = await getTask(taskId!);
        if (cancelled) return;
        setTask(t);
        if (t.status === "pending" || t.status === "running") {
          setTimeout(poll, 2000);
        }
      } catch (e: any) {
        if (cancelled) return;
        setError(e.message || "Failed to load task");
      }
    }

    poll();
    return () => { cancelled = true; };
  }, [taskId]);

  if (!taskId) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-20 text-center">
        <p className="font-display text-2xl italic text-muted-foreground">
          {lang === "zh" ? "未指定任務。從 /create 開始。" : "No task specified. Start from /create."}
        </p>
        <Button onClick={() => router.push("/create")} className="mt-6 rounded-full">
          {lang === "zh" ? "前往創建頁" : "Go to Create"}
        </Button>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-20 space-y-4">
        <div className="flex items-start gap-3 rounded-sm border border-destructive/40 bg-destructive/5 p-6">
          <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
          <div>
            <div className="font-display text-base font-medium">{lang === "zh" ? "任務加載失敗" : "Failed to load task"}</div>
            <div className="text-sm text-muted-foreground mt-1">{error}</div>
          </div>
        </div>
        <Button variant="outline" onClick={() => router.push("/create")} className="rounded-full">
          {lang === "zh" ? "返回創建" : "Back to Create"}
        </Button>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-20 text-center">
        <Loader2 className="inline h-6 w-6 animate-spin text-muted-foreground" />
        <p className="font-display text-base italic text-muted-foreground mt-3">
          {lang === "zh" ? "加載任務中…" : "Loading task…"}
        </p>
      </div>
    );
  }

  const isRunning = task.status === "pending" || task.status === "running";
  const isDone = task.status === "done";
  const isFailed = task.status === "failed";
  const stream = streamUrl(task.output_path);
  const download = downloadUrl(task.output_path);

  const currentStageIndex = isRunning
    ? Math.max(0, STAGES.findIndex(s => s.name === task.current_stage))
    : isDone ? STAGES.length - 1 : -1;

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-12 lg:py-14 space-y-10">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between animate-fade-up">
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-xs uppercase tracking-[0.2em] text-muted-foreground">
            <span className="font-display italic">Project</span>
            <span className="h-px w-12 bg-border" />
            <span className="tabular-nums">No. {task.id.slice(0, 6)}</span>
            <span className="font-display italic">
              {task.status === "running" ? "Rendering" : task.status === "pending" ? "Queued" : task.status === "done" ? "Complete" : "Failed"}
            </span>
          </div>
          <h1 className="font-display text-5xl font-medium tracking-tight lg:text-6xl">
            <span className="italic text-primary">{(task.script?.title || task.topic).slice(0, 30)}</span>
            {(task.script?.title || task.topic).length > 30 ? "…" : "."}
          </h1>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 font-display text-xs italic text-muted-foreground pt-1">
            <span>{task.aspect}</span>
            <span>·</span>
            <span>{Math.round(task.duration || 0)}s</span>
            <span>·</span>
            <span>{(task.file_size ? `${(task.file_size / 1024 / 1024).toFixed(1)} MB` : "—")}</span>
            <span>·</span>
            <span>{task.id.slice(0, 8)}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="rounded-full gap-2" onClick={() => router.push("/history")}>
            <ArrowLeft className="h-4 w-4" />{lang === "zh" ? "歷史" : "History"}
          </Button>
          {isDone && download && (
            <a href={download} target="_blank" rel="noopener">
              <Button className="rounded-full gap-2 bg-primary text-primary-foreground shadow-lg shadow-primary/30">
                <Download className="h-4 w-4" />{lang === "zh" ? "下載" : "Download"}
              </Button>
            </a>
          )}
        </div>
      </header>

      {isFailed && task.error && (
        <Card className="border-destructive/40 bg-destructive/5 p-5">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
            <div>
              <div className="font-display text-base font-medium">{lang === "zh" ? "任務失敗" : "Task failed"}</div>
              <div className="text-sm text-muted-foreground mt-1 font-mono">{task.error}</div>
            </div>
          </div>
        </Card>
      )}

      {/* Stage Progress */}
      {isRunning && (
        <Card className="border-border/60 bg-card/60 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Pipeline</p>
              <h2 className="font-display text-xl font-medium mt-1">
                {lang === "zh" ? "渲染中" : "Rendering"} · {task.progress}%
              </h2>
            </div>
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          </div>
          <div className="h-1.5 rounded-full bg-muted overflow-hidden mb-6">
            <div className="h-full bg-gradient-to-r from-primary to-amber-500 transition-all duration-700 ease-out" style={{ width: `${task.progress}%` }} />
          </div>
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
            {STAGES.map((s, i) => {
              const done = i < currentStageIndex;
              const active = i === currentStageIndex;
              return (
                <div
                  key={s.name}
                  className={cn(
                    "rounded-sm border p-3 transition-all",
                    done && "border-primary/40 bg-primary/5",
                    active && "border-primary bg-primary/10 ring-1 ring-primary/30",
                    !done && !active && "border-border/40 bg-card/40 opacity-50"
                  )}
                >
                  <div className="font-display text-[9px] uppercase tracking-widest text-muted-foreground">{s.num}</div>
                  <div className="font-display text-sm font-medium mt-1">{s.zh}</div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Main content */}
      <div className="grid gap-8 lg:grid-cols-12 animate-fade-up" style={{ animationDelay: "0.1s" }}>
        {/* LEFT: Script segments */}
        <Card className="lg:col-span-5 border-border/60 bg-card/60 backdrop-blur p-7">
          <div className="flex items-baseline justify-between mb-5">
            <h2 className="font-display text-xl font-medium">
              {lang === "zh" ? "腳本" : "Script"}
              {task.script && <span className="italic text-muted-foreground"> · {task.script.segments.length}</span>}
            </h2>
          </div>

          {task.script && task.script.segments.length > 0 ? (
            <ol className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
              {task.script.segments.map((s, i) => (
                <li
                  key={s.id}
                  className="rounded-sm border border-border/60 bg-background/40 p-4 animate-fade-up"
                  style={{ animationDelay: `${i * 0.05}s` }}
                >
                  <div className="flex items-baseline gap-3">
                    <span className="font-display text-xs italic text-muted-foreground tabular-nums w-6">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-display text-base font-medium">{lang === "zh" ? `段落 ${i + 1}` : `Segment ${i + 1}`}</h3>
                        <Badge variant="outline" className="rounded-full text-[9px] font-display border-border/60">
                          {Math.round(s.duration)}s
                        </Badge>
                      </div>
                      <p className="mt-1.5 text-sm leading-relaxed text-foreground/70">{s.text}</p>
                      {s.keyword && (
                        <p className="mt-1 text-xs text-muted-foreground italic font-display">
                          keyword: {s.keyword}
                        </p>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <div className="text-sm text-muted-foreground italic font-display text-center py-8">
              {isRunning ? (lang === "zh" ? "腳本生成中…" : "Script generating…") : (lang === "zh" ? "尚無腳本" : "No script yet")}
            </div>
          )}
        </Card>

        {/* CENTER: Preview */}
        <Card className="lg:col-span-4 border-border/60 bg-card/60 backdrop-blur p-7">
          <div className="flex items-baseline justify-between mb-5">
            <h2 className="font-display text-xl font-medium">{lang === "zh" ? "預覽" : "Preview"}</h2>
            <span className="font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground tabular-nums">
              {task.duration ? `00:${String(Math.round(task.duration)).padStart(2, "0")}` : "—"}
            </span>
          </div>

          <div className="mx-auto max-w-[240px]">
            <div className="aspect-[9/16] rounded-sm bg-gradient-to-br from-stone-300 via-amber-100 to-orange-100 relative overflow-hidden border border-border/60 film-grain shadow-2xl shadow-stone-900/20">
              {isDone && stream ? (
                <video src={stream} className="absolute inset-0 h-full w-full object-cover" controls muted loop preload="metadata" />
              ) : (
                <>
                  <div className="absolute inset-x-0 bottom-14 px-4 text-center">
                    <div className="font-display text-base italic text-foreground leading-snug drop-shadow-sm">
                      {task.script?.segments[0]?.text?.slice(0, 30) || "—"}
                    </div>
                  </div>
                  {isRunning && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/30 backdrop-blur-sm">
                      <Loader2 className="h-8 w-8 animate-spin text-white" />
                    </div>
                  )}
                </>
              )}
              <div className="absolute top-3 left-3 right-3 flex items-center justify-between font-display text-[9px] uppercase tracking-widest text-foreground/70">
                <span>{task.aspect}</span>
                <span className="italic tabular-nums">{Math.round(task.progress)}%</span>
              </div>
            </div>
          </div>

          {isDone && (
            <div className="mt-5 flex items-center justify-center gap-3">
              <Button size="icon" className="h-12 w-12 rounded-full bg-foreground text-background hover:bg-primary hover:text-primary-foreground shadow-lg">
                <Play className="h-5 w-5 ml-0.5" />
              </Button>
              <Button variant="ghost" size="icon" className="h-9 w-9 rounded-full">
                <Volume2 className="h-4 w-4" />
              </Button>
            </div>
          )}
        </Card>

        {/* RIGHT: Parameters */}
        <div className="lg:col-span-3 space-y-4">
          <Card className="border-border/60 bg-card/60 backdrop-blur p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Mic className="h-3.5 w-3.5 text-primary" />
                <h3 className="font-display text-sm font-medium">{lang === "zh" ? "配音" : "Voice"}</h3>
              </div>
            </div>
            <div className="space-y-1.5 font-display text-xs">
              <div className="flex items-baseline justify-between">
                <span className="italic text-muted-foreground">Service</span>
                <span className="font-medium">{task.config?.voice.provider || "edge"}</span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="italic text-muted-foreground">Voice</span>
                <span className="font-medium truncate ml-2">{task.config?.voice.voice_id?.split("-").slice(-1)[0] || "—"}</span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="italic text-muted-foreground">Speed</span>
                <span className="font-medium">{task.config?.voice.speed || "1.0"}x</span>
              </div>
            </div>
          </Card>

          <Card className="border-border/60 bg-card/60 backdrop-blur p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Type className="h-3.5 w-3.5 text-primary" />
                <h3 className="font-display text-sm font-medium">{lang === "zh" ? "字幕" : "Subtitle"}</h3>
              </div>
            </div>
            <div className="space-y-1.5 font-display text-xs">
              <div className="flex items-baseline justify-between">
                <span className="italic text-muted-foreground">Font</span>
                <span className="font-medium truncate ml-2">{task.config?.subtitle.font || "Noto Sans CJK SC"}</span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="italic text-muted-foreground">Position</span>
                <span className="font-medium">{task.config?.subtitle.position || "bottom"}</span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="italic text-muted-foreground">Size</span>
                <span className="font-medium">{task.config?.subtitle.font_size || 48}</span>
              </div>
            </div>
          </Card>

          <Card className="border-border/60 bg-card/60 backdrop-blur p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <ImageIcon className="h-3.5 w-3.5 text-primary" />
                <h3 className="font-display text-sm font-medium">{lang === "zh" ? "素材" : "Footage"}</h3>
              </div>
            </div>
            <div className="space-y-1.5 font-display text-xs">
              <div className="flex items-baseline justify-between">
                <span className="italic text-muted-foreground">Source</span>
                <span className="font-medium">{task.config?.material.provider || "pexels"}</span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="italic text-muted-foreground">Orientation</span>
                <span className="font-medium">{task.config?.material.orientation || "portrait"}</span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="italic text-muted-foreground">Segments</span>
                <span className="font-medium tabular-nums">{task.script?.segments.length || "—"}</span>
              </div>
            </div>
          </Card>

          <Card className="border-border/60 bg-card/60 backdrop-blur p-5">
            <div className="flex items-center gap-2 mb-3">
              <Music className="h-3.5 w-3.5 text-primary" />
              <h3 className="font-display text-sm font-medium">BGM</h3>
            </div>
            <div className="space-y-1.5 font-display text-xs">
              <div className="flex items-baseline justify-between">
                <span className="italic text-muted-foreground">Enabled</span>
                <span className="font-medium">{task.config?.bgm.enabled ? "Yes" : "No"}</span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="italic text-muted-foreground">Volume</span>
                <span className="font-medium tabular-nums">{Math.round((task.config?.bgm.volume || 0.3) * 100)}%</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function WorkspacePage() {
  return (
    <Suspense fallback={<div className="p-10 text-center font-display italic text-muted-foreground">Loading…</div>}>
      <WorkspaceInner />
    </Suspense>
  );
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(" ");
}