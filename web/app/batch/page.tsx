"use client";

import { useLang } from "@/lib/i18n";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Plus, Upload, ListTodo, Loader2, CheckCircle2, XCircle, FileJson } from "lucide-react";

export default function BatchPage() {
  const { t, lang } = useLang();

  const jobs = [
    { name: "October Series · 30 reels", status: "running", progress: 64, count: "18/30", time: lang === "zh" ? "5 分鐘前" : "5m ago" },
    { name: "Coffee brand collection · 12 reels", status: "running", progress: 25, count: "3/12", time: lang === "zh" ? "12 分鐘前" : "12m ago" },
    { name: "Lifestyle batch · 50 reels", status: "queued", progress: 0, count: "0/50", time: lang === "zh" ? "排隊中" : "Queued" },
    { name: "Summer promo · 8 reels", status: "done", progress: 100, count: "8/8", time: lang === "zh" ? "2 小時前" : "2h ago" },
    { name: "Travel vlog batch · 20 reels", status: "done", progress: 100, count: "20/20", time: lang === "zh" ? "昨天" : "Yesterday" },
    { name: "Quick test · 5 reels", status: "failed", progress: 40, count: "2/5", time: lang === "zh" ? "昨天" : "Yesterday" },
  ];

  const statusMap = {
    running: { icon: Loader2, label: t("batch_status_running"), variant: "default" as const, spin: true, color: "text-primary" },
    queued: { icon: ListTodo, label: t("batch_status_queued"), variant: "outline" as const, spin: false, color: "text-muted-foreground" },
    done: { icon: CheckCircle2, label: t("batch_status_done"), variant: "success" as const, spin: false, color: "text-emerald-500" },
    failed: { icon: XCircle, label: t("batch_status_failed"), variant: "destructive" as const, spin: false, color: "text-destructive" },
  };

  return (
    <div className="mx-auto max-w-7xl p-6 lg:p-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t("batch_title")}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {lang === "zh" ? "單批最多 100 個任務，每批 ≤ 1 MiB。" : "Max 100 tasks per batch, ≤ 1 MiB."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="gap-2"><FileJson className="h-4 w-4" />{t("batch_import")}</Button>
          <Button className="gap-2"><Plus className="h-4 w-4" />{t("batch_new")}</Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-3 sm:grid-cols-4">
        {[
          { label: lang === "zh" ? "活躍任務" : "Active", value: "2", color: "text-primary" },
          { label: lang === "zh" ? "排隊" : "Queued", value: "1", color: "text-amber-500" },
          { label: lang === "zh" ? "本月完成" : "Done this month", value: "238", color: "text-emerald-500" },
          { label: lang === "zh" ? "成功率" : "Success rate", value: "97.2%", color: "text-cyan-500" },
        ].map(s => (
          <Card key={s.label} className="p-4">
            <div className="text-xs text-muted-foreground">{s.label}</div>
            <div className={`text-2xl font-semibold tabular-nums mt-1 ${s.color}`}>{s.value}</div>
          </Card>
        ))}
      </div>

      {/* Task list */}
      <Card>
        <CardHeader>
          <CardTitle>{lang === "zh" ? "任務列表" : "Tasks"}</CardTitle>
          <CardDescription>{jobs.length} {lang === "zh" ? "個任務" : "jobs"}</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y">
            {jobs.map((j, i) => {
              const s = statusMap[j.status as keyof typeof statusMap];
              const Icon = s.icon;
              return (
                <div key={i} className="flex items-center gap-4 p-4 hover:bg-accent/30 transition-colors">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-md ${j.status === "running" ? "bg-primary/10" : j.status === "failed" ? "bg-destructive/10" : j.status === "done" ? "bg-emerald-500/10" : "bg-muted"}`}>
                    <Icon className={`h-5 w-5 ${s.color} ${s.spin ? "animate-spin" : ""}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm truncate">{j.name}</span>
                      <Badge variant={s.variant} className="text-[10px]">{s.label}</Badge>
                    </div>
                    <div className="mt-1.5 flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{j.count}</span>
                      <span>·</span>
                      <span>{j.time}</span>
                      <div className="flex-1 max-w-xs">
                        <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${j.status === "failed" ? "bg-destructive" : j.status === "done" ? "bg-emerald-500" : "bg-primary"}`}
                            style={{ width: `${j.progress}%` }}
                          />
                        </div>
                      </div>
                      <span className="tabular-nums">{j.progress}%</span>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm">{lang === "zh" ? "詳情" : "Details"}</Button>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}