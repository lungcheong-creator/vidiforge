"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useLang } from "@/lib/i18n";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Send, Sparkles, ArrowRight, Loader2, AlertCircle, Wrench, Film,
} from "lucide-react";
import { agentChat, listAgentTools, type AgentToolCall } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Turn {
  role: "user" | "assistant";
  content: string;
  toolCalls?: AgentToolCall[];
  model?: string;
}

const QUICK = {
  zh: [
    "建立一支關於北歐家居的 30 秒短影片",
    "我最近做了哪些影片？",
    "給我幾個咖啡主題的英文素材關鍵詞",
  ],
  en: [
    "Make a 30s video about Nordic home decor",
    "What videos have I made recently?",
    "Give me English stock keywords for a coffee theme",
  ],
};

export default function AgentPage() {
  const { lang } = useLang();
  const router = useRouter();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tools, setTools] = useState<{ name: string; description: string }[]>([]);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listAgentTools().then(setTools).catch(() => {});
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, busy]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    setError(null);
    setInput("");

    const next: Turn[] = [...turns, { role: "user", content: trimmed }];
    setTurns(next);
    setBusy(true);

    try {
      const res = await agentChat(
        next.map((t) => ({ role: t.role, content: t.content })),
        "deepseek-flash"
      );
      setTurns([
        ...next,
        {
          role: "assistant",
          content: res.reply,
          toolCalls: res.tool_calls,
          model: res.model,
        },
      ]);
    } catch (e: any) {
      setError(e?.message || "Agent request failed");
    } finally {
      setBusy(false);
    }
  }

  const quick = QUICK[lang === "zh" ? "zh" : "en"];
  const createdTasks = turns
    .flatMap((t) => t.toolCalls ?? [])
    .filter((c) => c.tool === "create_video" && (c.result as any)?.task_id)
    .map((c) => (c.result as any).task_id as string);

  return (
    <div className="mx-auto max-w-6xl px-6 py-10 lg:px-12 lg:py-14 h-full flex flex-col space-y-8">
      <header className="animate-fade-up">
        <div className="flex items-center gap-3 text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">
          <span className="font-display italic">Concierge</span>
          <span className="h-px w-12 bg-border" />
          <span>DeepSeek V4.1 Flash</span>
        </div>
        <h1 className="font-display text-5xl font-medium tracking-tight lg:text-6xl">
          {lang === "zh" ? "與 AI" : "A Conversation"}
          <span className="italic text-primary">
            {" "}
            {lang === "zh" ? "對話" : "with the Atelier"}.
          </span>
        </h1>
        <p className="font-display text-base italic text-muted-foreground mt-3 max-w-xl">
          {lang === "zh"
            ? "直接用說話的方式建影片。助手會呼叫工具完成任務。"
            : "Talk your video into existence — the agent calls the tools for you."}
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_300px] flex-1">
        <Card className="flex flex-col overflow-hidden border-border/60 bg-card/40 backdrop-blur">
          <div className="flex-1 overflow-y-auto p-6 lg:p-8 space-y-6 min-h-[420px]">
            {turns.length === 0 && (
              <div className="text-center py-10">
                <Sparkles className="h-6 w-6 text-primary mx-auto mb-3" />
                <p className="font-display italic text-muted-foreground">
                  {lang === "zh" ? "說一個想法，例如…" : "Start with an idea, e.g.…"}
                </p>
              </div>
            )}

            {turns.map((t, i) => (
              <div
                key={i}
                className={cn("flex gap-4 animate-fade-up", t.role === "user" ? "flex-row-reverse" : "flex-row")}
              >
                <div
                  className={cn(
                    "flex h-9 w-9 shrink-0 items-center justify-center rounded-full font-display text-sm",
                    t.role === "assistant"
                      ? "bg-foreground text-background italic"
                      : "bg-secondary text-foreground"
                  )}
                >
                  {t.role === "user" ? "U" : "V"}
                </div>

                <div className={cn("flex-1 max-w-[78%]", t.role === "user" && "flex flex-col items-end")}>
                  <div className="flex items-baseline gap-2 mb-1.5 font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                    <span>{t.role === "user" ? "You" : "VidiForge"}</span>
                    {t.model && <span className="font-mono lowercase">{t.model}</span>}
                  </div>

                  <div
                    className={cn(
                      "rounded-sm p-4 leading-relaxed font-display text-[15px] whitespace-pre-wrap",
                      t.role === "user"
                        ? "bg-foreground text-background italic"
                        : "bg-background/60 border border-border/60"
                    )}
                  >
                    {t.content}
                  </div>

                  {t.toolCalls && t.toolCalls.length > 0 && (
                    <div className="mt-3 space-y-2 w-full">
                      {t.toolCalls.map((c, j) => {
                        const r = c.result as any;
                        return (
                          <div
                            key={j}
                            className="rounded-sm border border-border/60 bg-background/40 p-3 text-xs font-display"
                          >
                            <div className="flex items-center gap-2">
                              {c.tool === "create_video" ? (
                                <Film className="h-3.5 w-3.5 text-primary" />
                              ) : (
                                <Wrench className="h-3.5 w-3.5 text-muted-foreground" />
                              )}
                              <span className="font-mono text-[11px]">{c.tool}</span>
                              {r?.task_id && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="ml-auto h-6 rounded-full px-2 text-[10px] gap-1"
                                  onClick={() => router.push(`/workspace?task_id=${r.task_id}`)}
                                >
                                  {lang === "zh" ? "查看" : "Open"}
                                  <ArrowRight className="h-3 w-3" />
                                </Button>
                              )}
                            </div>
                            <pre className="mt-1.5 whitespace-pre-wrap break-all text-muted-foreground">
                              {JSON.stringify(r, null, 0).slice(0, 220)}
                            </pre>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {busy && (
              <div className="flex gap-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-foreground text-background font-display text-sm italic">
                  V
                </div>
                <div className="rounded-sm bg-background/60 border border-border/60 px-4 py-3">
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          <div className="border-t border-border/60 p-4 bg-background/40">
            {error && (
              <div className="flex items-start gap-2 mb-3 rounded-sm border border-destructive/40 bg-destructive/5 p-3 text-xs">
                <AlertCircle className="h-3.5 w-3.5 text-destructive shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}
            <div className="flex flex-wrap gap-2 mb-3">
              {quick.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  disabled={busy}
                  className="font-display text-xs italic rounded-full border border-border/60 bg-background/60 hover:bg-secondary/40 hover:border-primary/40 px-3 py-1.5 transition-all disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send(input);
                  }
                }}
                placeholder={lang === "zh" ? "告訴助手你想做什麼…" : "Tell the agent what you want…"}
                disabled={busy}
                className="flex-1 h-11 rounded-full border border-border/60 bg-background px-5 font-display text-sm placeholder:italic placeholder:text-muted-foreground/60 focus:outline-none focus:border-primary/50 transition-colors disabled:opacity-60"
              />
              <Button
                onClick={() => send(input)}
                disabled={!input.trim() || busy}
                className="h-11 rounded-full bg-foreground text-background hover:bg-primary hover:text-primary-foreground px-5"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </Card>

        <div className="space-y-4">
          {createdTasks.length > 0 && (
            <Card className="border-border/60 bg-card/40 p-5">
              <p className="font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                {lang === "zh" ? "本次建立" : "Created here"}
              </p>
              <div className="mt-3 space-y-2">
                {createdTasks.map((id) => (
                  <button
                    key={id}
                    onClick={() => router.push(`/workspace?task_id=${id}`)}
                    className="w-full flex items-center justify-between rounded-sm border border-border/60 bg-background/50 px-3 py-2 text-xs font-mono hover:border-primary/50 transition-colors"
                  >
                    {id.slice(0, 12)}…
                    <ArrowRight className="h-3 w-3" />
                  </button>
                ))}
              </div>
            </Card>
          )}

          <Card className="border-border/60 bg-card/40 p-5">
            <p className="font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
              {lang === "zh" ? "可用工具" : "Tools"}
            </p>
            <ul className="mt-3 space-y-2.5">
              {tools.map((t) => (
                <li key={t.name}>
                  <div className="font-mono text-[11px] text-primary">{t.name}</div>
                  <div className="text-xs text-muted-foreground leading-relaxed">{t.description}</div>
                </li>
              ))}
              {tools.length === 0 && (
                <li className="text-xs text-muted-foreground italic">
                  {lang === "zh" ? "載入中…" : "Loading…"}
                </li>
              )}
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}
