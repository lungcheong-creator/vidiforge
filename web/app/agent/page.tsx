"use client";

import { useState } from "react";
import { useLang } from "@/lib/i18n";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Send, Sparkles, User, Bot, ChevronRight, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export default function AgentPage() {
  const { t, lang } = useLang();
  const [messages, setMessages] = useState<Array<{ role: "user" | "agent"; text: string; tool?: string }>>([
    { role: "agent", text: lang === "zh" ? "你好，我是 VidiForge 助手。我可以幫你生成視頻、編輯素材、翻譯腳本、批量處理。直接告訴我你想做什麼？" : "Hello. I'm VidiForge Agent. I can generate videos, edit footage, translate scripts, or batch-process. What shall we make today?", tool: "intro" },
  ]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);

  const quick = [
    t("agent_quick_1"),
    t("agent_quick_2"),
    t("agent_quick_3"),
  ];

  function send(text: string) {
    if (!text.trim()) return;
    setMessages(m => [...m, { role: "user", text }]);
    setInput("");
    setThinking(true);
    setTimeout(() => {
      setMessages(m => [...m, {
        role: "agent",
        text: lang === "zh"
          ? "好的，我來幫你創建。先分析主題，然後生成 5 段腳本，從 Pexels 匹配素材，使用 Edge TTS 配音，最後渲染。整個過程大約 90 秒。"
          : "Certainly. I'll analyze the subject, craft a 5-segment script, source footage from Pexels, voice it with Edge TTS, then render. ETA ~90s.",
        tool: "plan",
      }]);
      setThinking(false);
    }, 1200);
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-10 lg:px-12 lg:py-14 h-full flex flex-col space-y-10">
      {/* ========== EDITORIAL HEADER ========== */}
      <header className="animate-fade-up">
        <div className="flex items-center gap-3 text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">
          <span className="font-display italic">Concierge</span>
          <span className="h-px w-12 bg-border" />
          <span className="tabular-nums">№ 006</span>
          <span className="font-display italic">AI</span>
        </div>
        <h1 className="font-display text-5xl font-medium tracking-tight lg:text-6xl">
          {lang === "zh" ? "與 AI" : "A Conversation"}
          <span className="italic text-primary"> {lang === "zh" ? "對話" : "with the Atelier"}.</span>
        </h1>
        <p className="font-display text-base italic text-muted-foreground mt-3 max-w-xl">
          {lang === "zh"
            ? "用對話驅動整個創作流程。"
            : "Drive the entire creation through conversation."}
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px] flex-1">
        {/* ========== CONVERSATION ========== */}
        <Card className="flex flex-col overflow-hidden border-border/60 bg-card/40 backdrop-blur">
          {/* Messages area */}
          <div className="flex-1 overflow-y-auto p-8 lg:p-10 space-y-8 min-h-[500px]">
            {messages.map((m, i) => (
              <div
                key={i}
                className={cn(
                  "flex gap-5 animate-fade-up",
                  m.role === "user" ? "flex-row-reverse" : "flex-row"
                )}
                style={{ animationDelay: `${i * 0.05}s` }}
              >
                {m.role === "agent" ? (
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-foreground text-background font-display text-base italic">
                    V
                  </div>
                ) : (
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary text-foreground">
                    <User className="h-4 w-4" />
                  </div>
                )}

                <div className={cn("flex-1 max-w-[78%]", m.role === "user" && "flex flex-col items-end")}>
                  <div className="flex items-baseline gap-2 mb-1.5 font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                    <span>{m.role === "agent" ? "VidiForge" : "You"}</span>
                    <span className="tabular-nums">{String(i + 1).padStart(2, "0")}</span>
                    {m.tool && m.tool !== "intro" && (
                      <Badge variant="outline" className="rounded-full text-[9px] ml-1 font-mono">
                        {m.tool === "plan" ? "video.create" : m.tool}
                      </Badge>
                    )}
                  </div>
                  <div className={cn(
                    "rounded-sm p-5 leading-relaxed font-display text-base",
                    m.role === "user"
                      ? "bg-foreground text-background italic"
                      : "bg-background/60 border border-border/60"
                  )}>
                    {m.text}
                  </div>

                  {/* Plan steps */}
                  {m.tool === "plan" && (
                    <div className="mt-4 rounded-sm border border-border/60 bg-background/40 p-5 space-y-2.5">
                      {[
                        { name: "subject_analysis", label: lang === "zh" ? "主題分析" : "Subject", state: "done" },
                        { name: "script_generate", label: lang === "zh" ? "腳本生成" : "Script", state: "done" },
                        { name: "footage_match", label: lang === "zh" ? "素材匹配" : "Footage", state: "running" },
                        { name: "voice_over", label: lang === "zh" ? "配音" : "Voice", state: "queued" },
                        { name: "subtitle", label: lang === "zh" ? "字幕" : "Subtitle", state: "queued" },
                        { name: "render", label: lang === "zh" ? "渲染" : "Render", state: "queued" },
                      ].map((s, j) => (
                        <div key={j} className="flex items-center gap-3 text-sm font-display">
                          {s.state === "done" && (
                            <>
                              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                              <span className="line-through text-muted-foreground">{s.label}</span>
                            </>
                          )}
                          {s.state === "running" && (
                            <>
                              <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                              <span className="font-medium text-primary">{s.label}</span>
                            </>
                          )}
                          {s.state === "queued" && (
                            <>
                              <span className="h-1.5 w-1.5 rounded-full bg-border" />
                              <span className="text-muted-foreground">{s.label}</span>
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {thinking && (
              <div className="flex gap-5 animate-fade-up">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-foreground text-background font-display text-base italic">
                  V
                </div>
                <div className="rounded-sm bg-background/60 border border-border/60 px-5 py-4">
                  <div className="flex gap-1.5">
                    <div className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40 animate-bounce" style={{ animationDelay: "0ms" }} />
                    <div className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40 animate-bounce" style={{ animationDelay: "150ms" }} />
                    <div className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40 animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="border-t border-border/60 p-5 bg-background/40">
            <div className="flex flex-wrap gap-2 mb-3">
              {quick.map((q, i) => (
                <button
                  key={i}
                  onClick={() => send(q)}
                  className="font-display text-xs italic rounded-full border border-border/60 bg-background/60 hover:bg-secondary/40 hover:border-primary/40 px-3.5 py-1.5 transition-all"
                >
                  {q}
                </button>
              ))}
            </div>
            <div className="flex gap-3">
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && send(input)}
                placeholder={t("agent_placeholder")}
                className="flex-1 h-12 rounded-full border border-border/60 bg-background px-6 font-display text-sm placeholder:italic placeholder:text-muted-foreground/60 focus:outline-none focus:border-primary/50 transition-colors"
              />
              <Button
                onClick={() => send(input)}
                disabled={!input.trim()}
                className="h-12 rounded-full bg-foreground text-background hover:bg-primary hover:text-primary-foreground px-6"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </Card>

        {/* ========== SIDE PANEL ========== */}
        <div className="space-y-4">
          <Card className="border-border/60 bg-card/40 p-6">
            <p className="font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Active Plan</p>
            <h3 className="font-display text-xl font-medium mt-1.5">
              {lang === "zh" ? "早晨習慣" : "Morning Routine"}
            </h3>
            <p className="text-sm text-muted-foreground mt-1 italic font-display">
              {lang === "zh" ? "30 秒 · 6 段腳本" : "30s · 6 segments"}
            </p>
            <div className="mt-5 space-y-3">
              <div>
                <div className="flex justify-between text-xs font-display mb-1.5">
                  <span className="italic text-muted-foreground">Progress</span>
                  <span className="tabular-nums">34%</span>
                </div>
                <div className="h-1 rounded-full bg-secondary overflow-hidden">
                  <div className="h-full w-1/3 bg-primary rounded-full transition-all" />
                </div>
              </div>
              <div className="pt-2 border-t border-border/60 space-y-1.5 font-display text-xs">
                <div className="flex justify-between">
                  <span className="italic text-muted-foreground">{lang === "zh" ? "已用" : "Used"}</span>
                  <span>14s / 90s</span>
                </div>
                <div className="flex justify-between">
                  <span className="italic text-muted-foreground">{lang === "zh" ? "剩餘" : "Remaining"}</span>
                  <span>76s</span>
                </div>
              </div>
            </div>
            <Button className="w-full mt-5 rounded-full gap-2" variant="outline">
              {lang === "zh" ? "查看詳情" : "View Details"}
              <ChevronRight className="h-3.5 w-3.5" />
            </Button>
          </Card>

          <Card className="border-border/60 bg-card/40 p-6">
            <p className="font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">{lang === "zh" ? "能力" : "Capabilities"}</p>
            <ul className="mt-3 space-y-2 text-sm font-display">
              {[
                lang === "zh" ? "生成完整短視頻" : "Generate a complete reel",
                lang === "zh" ? "編輯現有項目" : "Edit existing projects",
                lang === "zh" ? "翻譯並重新配音" : "Translate & re-voice",
                lang === "zh" ? "批量處理多個任務" : "Batch process tasks",
                lang === "zh" ? "優化提示詞" : "Refine prompts",
              ].map((c) => (
                <li key={c} className="flex items-baseline gap-2 text-foreground/80">
                  <span className="text-primary">·</span>
                  <span className="italic">{c}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}