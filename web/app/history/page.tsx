"use client";

import { useEffect, useState } from "react";
import { useLang } from "@/lib/i18n";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, Eye, Search, Grid3X3, List, AlertCircle, RefreshCw } from "lucide-react";
import { listTasks, streamUrl, downloadUrl } from "@/lib/api";
import type { VideoTask } from "@vidiforge/shared";
import { cn } from "@/lib/utils";

const PALETTE = [
  "from-stone-200 via-amber-100 to-orange-100",
  "from-rose-400 to-orange-400",
  "from-emerald-50 via-stone-100 to-stone-200",
  "from-indigo-100 via-stone-200 to-stone-300",
  "from-amber-100 via-orange-100 to-rose-100",
];

export default function HistoryPage() {
  const { t, lang } = useLang();
  const [filter, setFilter] = useState<"all" | "done" | "failed">("all");
  const [view, setView] = useState<"grid" | "list">("grid");
  const [tasks, setTasks] = useState<VideoTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const res = await listTasks(100, 0);
      setTasks(res.tasks);
    } catch (e: any) {
      setError(e.message || "Failed to load tasks");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  const filtered = tasks.filter(t =>
    (filter === "all" || t.status === filter) &&
    (!search || t.topic.toLowerCase().includes(search.toLowerCase()))
  );

  const filters = [
    { k: "all", l: t("hist_filter_all") },
    { k: "done", l: t("hist_filter_done") },
    { k: "failed", l: t("hist_filter_failed") },
  ];

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-12 lg:py-14 space-y-8 animate-fade-up">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-xs uppercase tracking-[0.2em] text-muted-foreground">
            <span className="font-display italic">Archive</span>
            <span className="h-px w-12 bg-border" />
            <span className="tabular-nums">No. 005</span>
            <span className="font-display italic">Reels</span>
          </div>
          <h1 className="font-display text-5xl font-medium tracking-tight lg:text-6xl">
            {t("hist_title")}<span className="italic text-primary">.</span>
          </h1>
          <p className="font-display italic text-muted-foreground">
            {lang === "zh" ? `${filtered.length} 個成片 · ${tasks.length} 個任務` : `${filtered.length} videos · ${tasks.length} tasks`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={refresh} className="h-9 w-9 rounded-full">
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          </Button>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              placeholder={lang === "zh" ? "搜索…" : "Search…"}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-9 w-48 rounded-full border border-border bg-secondary/40 pr-3 pl-9 text-xs placeholder:text-muted-foreground focus:outline-none focus:border-primary/50"
            />
          </div>
          <div className="flex border rounded-full">
            <Button variant={view === "grid" ? "secondary" : "ghost"} size="icon" className="h-9 w-9 rounded-l-full rounded-r-none" onClick={() => setView("grid")}>
              <Grid3X3 className="h-4 w-4" />
            </Button>
            <Button variant={view === "list" ? "secondary" : "ghost"} size="icon" className="h-9 w-9 rounded-r-full rounded-l-none" onClick={() => setView("list")}>
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {error && (
        <Card className="border-destructive/40 bg-destructive/5 p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
            <div>
              <div className="font-display text-sm font-medium">{lang === "zh" ? "加載失敗" : "Failed to load tasks"}</div>
              <div className="text-xs text-muted-foreground mt-1">{error}</div>
            </div>
          </div>
        </Card>
      )}

      {/* Filter tabs */}
      <div className="flex items-center gap-1 border-b border-border/60">
        {filters.map(f => (
          <button
            key={f.k}
            onClick={() => setFilter(f.k as typeof filter)}
            className={cn(
              "px-3 py-2 text-sm font-display transition-colors relative",
              filter === f.k ? "text-foreground font-medium" : "text-muted-foreground hover:text-foreground"
            )}
          >
            {f.l}
            {filter === f.k && <div className="absolute -bottom-px left-0 right-0 h-0.5 bg-primary" />}
          </button>
        ))}
      </div>

      {loading && tasks.length === 0 ? (
        <Card className="border-border/60 bg-card/40 p-12 text-center">
          <div className="font-display italic text-muted-foreground">{lang === "zh" ? "加載中…" : "Loading…"}</div>
        </Card>
      ) : filtered.length === 0 ? (
        <Card className="border-border/60 bg-card/40 p-12 text-center">
          <div className="font-display text-2xl italic text-muted-foreground">
            {lang === "zh" ? "尚無作品" : "No reels yet"}
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            {lang === "zh" ? "去 /create 頁面生成第一段成片。" : "Head to /create to generate your first reel."}
          </p>
        </Card>
      ) : view === "grid" ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((task, i) => {
            const palette = PALETTE[i % PALETTE.length];
            const stream = streamUrl(task.output_path);
            const download = downloadUrl(task.output_path);
            return (
              <Card key={task.id} className="overflow-hidden border-border/60 hover-lift group">
                <div className={`aspect-video bg-gradient-to-br ${palette} relative film-grain`}>
                  {stream && task.status === "done" ? (
                    <video src={stream} className="absolute inset-0 h-full w-full object-cover" muted preload="metadata" />
                  ) : null}
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
                    {download && (
                      <a href={download} target="_blank" rel="noopener">
                        <Button size="sm" className="h-8 gap-1 rounded-full">
                          <Download className="h-3.5 w-3.5" /> {t("hist_download")}
                        </Button>
                      </a>
                    )}
                  </div>
                  <div className="absolute top-2 left-2 flex gap-1">
                    <Badge variant="secondary" className="bg-black/50 text-white border-0 backdrop-blur-sm text-[10px]">{task.aspect}</Badge>
                    {task.duration && <Badge variant="secondary" className="bg-black/50 text-white border-0 backdrop-blur-sm text-[10px]">{Math.round(task.duration)}s</Badge>}
                  </div>
                  <div className="absolute top-2 right-2">
                    {task.status === "done" && <Badge variant="success" className="text-[10px] rounded-full">{t("hist_filter_done")}</Badge>}
                    {task.status === "failed" && <Badge variant="destructive" className="text-[10px] rounded-full">{t("hist_filter_failed")}</Badge>}
                    {(task.status === "pending" || task.status === "running") && <Badge variant="secondary" className="text-[10px] rounded-full">{task.status}</Badge>}
                  </div>
                </div>
                <CardContent className="p-3">
                  <div className="font-display text-sm font-medium line-clamp-1">{task.topic}</div>
                  <div className="mt-1 flex items-center justify-between text-xs text-muted-foreground tabular-nums">
                    <span>{task.file_size ? `${(task.file_size / 1024 / 1024).toFixed(1)} MB` : "—"}</span>
                    <span>{new Date(task.created_at).toLocaleDateString()}</span>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card className="border-border/60 bg-card/60 divide-y divide-border/60">
          {filtered.map((task, i) => {
            const palette = PALETTE[i % PALETTE.length];
            const stream = streamUrl(task.output_path);
            return (
              <div key={task.id} className="flex items-center gap-4 p-3 hover:bg-accent/40">
                <div className={`h-12 w-20 rounded-sm bg-gradient-to-br ${palette} shrink-0 film-grain`} />
                <div className="flex-1 min-w-0">
                  <div className="font-display text-sm font-medium truncate">{task.topic}</div>
                  <div className="text-xs text-muted-foreground font-display italic">
                    {task.aspect} · {Math.round(task.duration || 0)}s · {task.file_size ? `${(task.file_size / 1024 / 1024).toFixed(1)} MB` : "—"} · {new Date(task.created_at).toLocaleString()}
                  </div>
                </div>
                <Badge variant={task.status === "done" ? "success" : task.status === "failed" ? "destructive" : "secondary"} className="text-[10px] rounded-full">
                  {task.status}
                </Badge>
                {stream && (
                  <a href={stream} target="_blank" rel="noopener">
                    <Button variant="ghost" size="sm" className="gap-1 rounded-full">
                      <Eye className="h-3.5 w-3.5" />
                      {t("hist_preview")}
                    </Button>
                  </a>
                )}
              </div>
            );
          })}
        </Card>
      )}
    </div>
  );
}