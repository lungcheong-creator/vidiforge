"use client";

import { useCallback, useEffect, useState } from "react";
import { useLang } from "@/lib/i18n";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input, Textarea } from "@/components/ui/input";
import {
  Plus, ListTodo, Loader2, CheckCircle2, XCircle, RefreshCw,
  AlertCircle, Trash2, ChevronRight,
} from "lucide-react";
import { listBatches, createBatch, deleteBatch, type BatchSummary } from "@/lib/api";
import { cn } from "@/lib/utils";

const STATUS_STYLE = {
  running: { icon: Loader2, spin: true, label: "渲染中", variant: "default" as const, color: "text-primary" },
  pending: { icon: ListTodo, spin: false, label: "排隊中", variant: "outline" as const, color: "text-muted-foreground" },
  done: { icon: CheckCircle2, spin: false, label: "已完成", variant: "success" as const, color: "text-emerald-500" },
  failed: { icon: XCircle, spin: false, label: "部分失敗", variant: "destructive" as const, color: "text-destructive" },
};

export default function BatchPage() {
  const { lang } = useLang();
  const [batches, setBatches] = useState<BatchSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [topicsText, setTopicsText] = useState("");
  const [duration, setDuration] = useState(30);
  const [submitting, setSubmitting] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listBatches(50, 0);
      // hydrate per-task progress for batches that are still moving
      const hydrated = await Promise.all(
        res.batches.map(async (b) => {
          if (b.status === "running" || b.status === "pending") {
            try {
              const detail = await import("@/lib/api").then((m) => m.getBatch(b.id));
              return detail;
            } catch {
              return b;
            }
          }
          return b;
        })
      );
      setBatches(hydrated);
    } catch (e: any) {
      setError(e?.message || "Failed to load batches");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 8000);
    return () => clearInterval(id);
  }, [refresh]);

  async function handleCreate() {
    const topics = topicsText
      .split("\n")
      .map((t) => t.trim())
      .filter(Boolean);
    if (!name.trim() || topics.length === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      await createBatch({ name: name.trim(), topics, duration, segments: 5 });
      setName("");
      setTopicsText("");
      setShowForm(false);
      await refresh();
    } catch (e: any) {
      setError(e?.message || "Failed to create batch");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm(lang === "zh" ? "刪除此批次？（影片會保留）" : "Delete this batch? (videos are kept)"))
      return;
    try {
      await deleteBatch(id);
      await refresh();
    } catch (e: any) {
      setError(e?.message || "Failed to delete");
    }
  }

  const totalTasks = batches.reduce((n, b) => n + b.total, 0);
  const doneTasks = batches.reduce((n, b) => n + b.completed, 0);
  const failedTasks = batches.reduce((n, b) => n + b.failed, 0);
  const active = batches.filter((b) => b.status === "running" || b.status === "pending").length;
  const successRate = doneTasks + failedTasks > 0
    ? ((doneTasks / (doneTasks + failedTasks)) * 100).toFixed(1)
    : "—";

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-12 lg:py-14 space-y-8 animate-fade-up">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-xs uppercase tracking-[0.2em] text-muted-foreground">
            <span className="font-display italic">Batches</span>
            <span className="h-px w-12 bg-border" />
            <span className="tabular-nums">No. 004</span>
          </div>
          <h1 className="font-display text-5xl font-medium tracking-tight lg:text-6xl">
            {lang === "zh" ? "批量" : "Batch"}
            <span className="italic text-primary"> {lang === "zh" ? "任務" : "Tasks"}.</span>
          </h1>
          <p className="font-display italic text-muted-foreground">
            {lang === "zh"
              ? "單批最多 100 個主題，逐支依序生成。"
              : "Up to 100 topics per batch, rendered one at a time."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={refresh} className="h-9 w-9 rounded-full">
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          </Button>
          <Button
            onClick={() => setShowForm((v) => !v)}
            className="gap-2 rounded-full bg-primary text-primary-foreground"
          >
            <Plus className="h-4 w-4" />
            {lang === "zh" ? "新建批次" : "New batch"}
          </Button>
        </div>
      </header>

      {error && (
        <div className="flex items-start gap-3 rounded-sm border border-destructive/40 bg-destructive/5 p-4">
          <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {showForm && (
        <Card className="border-border/60 bg-card/60 p-6 space-y-4 animate-fade-up">
          <div className="grid gap-4 sm:grid-cols-[2fr_1fr]">
            <div>
              <label className="font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                {lang === "zh" ? "批次名稱" : "Batch name"}
              </label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={lang === "zh" ? "十月系列" : "October series"}
                className="mt-2 border-border/60 bg-background/50"
              />
            </div>
            <div>
              <label className="font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                {lang === "zh" ? "每支秒數" : "Seconds each"}
              </label>
              <Input
                type="number"
                value={String(duration)}
                onChange={(e) => setDuration(Number(e.target.value))}
                className="mt-2 border-border/60 bg-background/50"
              />
            </div>
          </div>
          <div>
            <label className="font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
              {lang === "zh" ? "主題（每行一個）" : "Topics (one per line)"}
            </label>
            <Textarea
              rows={5}
              value={topicsText}
              onChange={(e) => setTopicsText(e.target.value)}
              placeholder={
                lang === "zh"
                  ? "北歐家居五個技巧\n早晨咖啡儀式感\n極簡主義斷捨離"
                  : "Nordic home tips\nMorning coffee ritual\nMinimalist living"
              }
              className="mt-2 border-border/60 bg-background/50"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              {topicsText.split("\n").filter((t) => t.trim()).length} {lang === "zh" ? "個主題" : "topics"}
            </p>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" className="rounded-full" onClick={() => setShowForm(false)}>
              {lang === "zh" ? "取消" : "Cancel"}
            </Button>
            <Button
              onClick={handleCreate}
              disabled={submitting || !name.trim() || !topicsText.trim()}
              className="gap-2 rounded-full bg-primary text-primary-foreground"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              {lang === "zh" ? "開始批次" : "Start batch"}
            </Button>
          </div>
        </Card>
      )}

      <div className="grid gap-3 sm:grid-cols-4">
        {[
          { label: lang === "zh" ? "活躍批次" : "Active", value: String(active), color: "text-primary" },
          { label: lang === "zh" ? "任務總數" : "Total tasks", value: String(totalTasks), color: "text-foreground" },
          { label: lang === "zh" ? "已完成" : "Completed", value: String(doneTasks), color: "text-emerald-500" },
          { label: lang === "zh" ? "成功率" : "Success rate", value: successRate === "—" ? "—" : `${successRate}%`, color: "text-cyan-500" },
        ].map((s) => (
          <Card key={s.label} className="p-4 border-border/60 bg-card/60">
            <div className="text-xs text-muted-foreground font-display">{s.label}</div>
            <div className={cn("text-2xl font-semibold tabular-nums mt-1 font-display", s.color)}>{s.value}</div>
          </Card>
        ))}
      </div>

      {batches.length === 0 && !loading ? (
        <Card className="border-border/60 bg-card/40 p-12 text-center">
          <div className="font-display text-2xl italic text-muted-foreground">
            {lang === "zh" ? "尚無批次" : "No batches yet"}
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            {lang === "zh" ? "點右上「新建批次」開始。" : "Use “New batch” to get started."}
          </p>
        </Card>
      ) : (
        <Card className="border-border/60 bg-card/60 divide-y divide-border/60">
          {batches.map((b) => {
            const style = STATUS_STYLE[b.status] ?? STATUS_STYLE.pending;
            const Icon = style.icon;
            const pct = b.total ? Math.round(((b.completed + b.failed) / b.total) * 100) : 0;
            return (
              <div key={b.id} className="p-4 space-y-2 hover:bg-accent/30 transition-colors">
                <div className="flex items-center gap-4">
                  <div className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-full shrink-0",
                    b.status === "done" ? "bg-emerald-500/10" :
                    b.status === "failed" ? "bg-destructive/10" :
                    b.status === "running" ? "bg-primary/10" : "bg-muted"
                  )}>
                    <Icon className={cn("h-5 w-5", style.color, style.spin && "animate-spin")} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-display font-medium truncate">{b.name}</span>
                      <Badge variant={style.variant} className="text-[10px] rounded-full">
                        {style.label}
                      </Badge>
                      {b.failed > 0 && (
                        <Badge variant="destructive" className="text-[10px] rounded-full">
                          {b.failed} {lang === "zh" ? "失敗" : "failed"}
                        </Badge>
                      )}
                    </div>
                    <div className="mt-1.5 flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="tabular-nums">{b.completed + b.failed}/{b.total}</span>
                      <span>·</span>
                      <span>{new Date(b.created_at).toLocaleString()}</span>
                      <div className="flex-1 max-w-xs">
                        <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                          <div
                            className={cn(
                              "h-full rounded-full transition-all",
                              b.status === "failed" ? "bg-destructive" : b.status === "done" ? "bg-emerald-500" : "bg-primary"
                            )}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                      <span className="tabular-nums">{pct}%</span>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full" onClick={() => handleDelete(b.id)}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>

                {b.tasks && b.tasks.length > 0 && (
                  <div className="pl-14 space-y-1">
                    {b.tasks.map((t) => (
                      <div key={t.id} className="flex items-center gap-2 text-xs">
                        {t.status === "done" ? (
                          <CheckCircle2 className="h-3 w-3 text-emerald-500 shrink-0" />
                        ) : t.status === "failed" ? (
                          <XCircle className="h-3 w-3 text-destructive shrink-0" />
                        ) : t.status === "running" ? (
                          <Loader2 className="h-3 w-3 animate-spin text-primary shrink-0" />
                        ) : (
                          <ListTodo className="h-3 w-3 text-muted-foreground shrink-0" />
                        )}
                        <span className="truncate text-foreground/80">{t.topic}</span>
                        <span className="text-muted-foreground tabular-nums">{t.progress}%</span>
                        {t.error && <span className="text-destructive truncate">— {t.error.slice(0, 60)}</span>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </Card>
      )}
    </div>
  );
}
