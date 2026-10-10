"use client";

import { useLang } from "@/lib/i18n";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  ArrowRight, Film, Clock, Zap, Image as ImageIcon,
  Mic, Type, Music, Sparkles, CheckCircle2, AlertCircle, ArrowUpRight,
} from "lucide-react";
import Link from "next/link";

export default function Dashboard() {
  const { t, lang } = useLang();

  const greeting = (() => {
    const h = new Date().getHours();
    if (h < 12) return t("dash_greeting_morning");
    if (h < 18) return t("dash_greeting_afternoon");
    return t("dash_greeting_evening");
  })();

  const stats = [
    { label: t("dash_stats_videos"), value: "47", unit: "reels", delta: "+12", icon: Film },
    { label: t("dash_stats_minutes"), value: "128", unit: "minutes", delta: "+34", icon: Clock },
    { label: t("dash_stats_calls"), value: "1,842", unit: "calls", delta: "+18%", icon: Zap },
  ];

  const services = [
    { name: "OpenAI GPT-4o", role: lang === "zh" ? "腳本生成" : "Script", status: "ok" },
    { name: "Edge TTS", role: lang === "zh" ? "配音" : "Voice", status: "ok" },
    { name: "Pexels API", role: lang === "zh" ? "素材庫" : "Footage", status: "ok" },
    { name: "MiniMax", role: lang === "zh" ? "文生視頻" : "AI Video", status: "missing" },
    { name: "ElevenLabs", role: lang === "zh" ? "高品質配音" : "Premium TTS", status: "missing" },
  ];

  const recent = [
    {
      title: lang === "zh" ? "北歐家居五則" : "Nordic Home, Five Notes",
      subtitle: lang === "zh" ? "室內裝飾 · 生活方式" : "Interiors · Lifestyle",
      ratio: "9:16", dur: "30s", segs: 5,
      time: lang === "zh" ? "今晨" : "This morning",
      grad: "from-stone-200 via-stone-100 to-amber-100",
      accent: "#C45A3E",
    },
    {
      title: lang === "zh" ? "早晨咖啡儀式" : "Morning Coffee Ritual",
      subtitle: lang === "zh" ? "儀式感 · 慢生活" : "Ritual · Slow Living",
      ratio: "9:16", dur: "45s", segs: 6,
      time: lang === "zh" ? "昨日" : "Yesterday",
      grad: "from-amber-100 via-orange-100 to-rose-100",
      accent: "#A06030",
    },
    {
      title: lang === "zh" ? "極簡主義斷捨離" : "On Less, and Living",
      subtitle: lang === "zh" ? "哲學 · 居家" : "Philosophy · Home",
      ratio: "1:1", dur: "60s", segs: 8,
      time: lang === "zh" ? "三日" : "Three days",
      grad: "from-emerald-50 via-stone-100 to-stone-200",
      accent: "#5B5238",
    },
    {
      title: lang === "zh" ? "東京街頭夜景" : "Tokyo Streets at Night",
      subtitle: lang === "zh" ? "城市 · 旅行" : "Urban · Travel",
      ratio: "16:9", dur: "20s", segs: 4,
      time: lang === "zh" ? "上週" : "Last week",
      grad: "from-indigo-100 via-stone-200 to-stone-300",
      accent: "#3A3A5C",
    },
  ];

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-12 lg:py-14 space-y-14">
      {/* ========== HERO ========== */}
      <section className="grid gap-10 lg:grid-cols-[1.6fr_1fr] lg:gap-16 animate-fade-up">
        {/* Editorial greeting */}
        <div className="space-y-6">
          <div className="flex items-center gap-3 text-xs uppercase tracking-[0.2em] text-muted-foreground">
            <span className="font-display italic">No.</span>
            <span className="tabular-nums">001</span>
            <span className="h-px flex-1 bg-border" />
            <span>{new Date().toLocaleDateString(lang === "zh" ? "zh-CN" : "en-US", { weekday: "long" })}</span>
          </div>

          <h1 className="font-display text-5xl font-medium leading-[1.05] tracking-tight lg:text-7xl">
            {greeting},<br />
            <span className="italic text-primary">Michael.</span>
          </h1>

          <p className="font-display text-xl italic leading-relaxed text-foreground/70 lg:text-2xl max-w-xl">
            {lang === "zh"
              ? "從一個想法到一段成片——讓 AI 接管所有的繁瑣，留給你創作的純粹。"
              : "From a single thought to a finished reel—let AI handle the craft, so the making stays yours."}
          </p>

          {/* CTA */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link href="/create">
              <Button className="group h-12 rounded-full bg-primary px-7 text-sm font-medium text-primary-foreground shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 transition-all">
                <Sparkles className="mr-2 h-4 w-4" />
                {lang === "zh" ? "開始一個新項目" : "Begin a New Project"}
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
            <Link href="/history">
              <Button variant="ghost" className="group h-12 px-5 text-sm font-medium">
                {lang === "zh" ? "查看歷史" : "View Archive"}
                <ArrowUpRight className="ml-1 h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </Button>
            </Link>
          </div>
        </div>

        {/* Quick start - editorial card */}
        <Card className="border-border/60 bg-card/80 p-6 backdrop-blur hover-lift">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Quick Start</p>
              <h3 className="font-display text-lg font-medium mt-1">{lang === "zh" ? "一句話生成" : "From a Phrase"}</h3>
            </div>
            <span className="flex h-7 w-7 items-center justify-center rounded-full border border-border text-xs font-display tabular-nums">
              ✦
            </span>
          </div>

          <Textarea
            placeholder={lang === "zh" ? "例如：北歐風家居擺設的 5 個技巧" : "e.g. 5 styling tips for Nordic home decor"}
            rows={3}
            defaultValue=""
            className="resize-none border-0 bg-secondary/30 font-display text-sm italic placeholder:not-italic placeholder:text-muted-foreground/60 focus-visible:ring-0 focus-visible:bg-secondary/50"
          />

          <div className="mt-4 flex flex-wrap items-center gap-1.5">
            {[
              { icon: ImageIcon, label: "9:16" },
              { icon: Mic, label: "Edge TTS" },
              { icon: Music, label: "BGM" },
              { icon: Type, label: lang === "zh" ? "字幕" : "Subs" },
            ].map((c) => (
              <Badge key={c.label} variant="outline" className="gap-1 border-border/60 bg-background/50 font-normal">
                <c.icon className="h-3 w-3" />
                {c.label}
              </Badge>
            ))}
            <Link href="/create" className="ml-auto">
              <Button size="sm" className="h-7 rounded-full px-3 text-xs">
                {t("dash_generate")}
                <ArrowRight className="ml-1 h-3 w-3" />
              </Button>
            </Link>
          </div>
        </Card>
      </section>

      {/* ========== STATS - Editorial row ========== */}
      <section className="border-y border-border/60 py-10 animate-fade-up" style={{ animationDelay: "0.1s" }}>
        <div className="grid gap-10 sm:grid-cols-3 sm:divide-x sm:divide-border/60">
          {stats.map((s, i) => {
            const Icon = s.icon;
            return (
              <div key={s.label} className={`space-y-2 ${i > 0 ? "sm:pl-10" : ""}`}>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Icon className="h-3.5 w-3.5" />
                  <span className="uppercase tracking-widest">{s.label}</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="font-display text-5xl font-medium tabular-nums tracking-tight">{s.value}</span>
                  <span className="font-display text-sm italic text-muted-foreground">{s.unit}</span>
                </div>
                <div className="flex items-center gap-1 text-xs">
                  <span className="text-primary font-medium tabular-nums">{s.delta}</span>
                  <span className="text-muted-foreground">{lang === "zh" ? "本月" : "this month"}</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ========== RECENT PROJECTS ========== */}
      <section className="space-y-6 animate-fade-up" style={{ animationDelay: "0.15s" }}>
        <div className="flex items-end justify-between">
          <div>
            <p className="font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Recently Made</p>
            <h2 className="font-display text-3xl font-medium tracking-tight mt-1">
              {lang === "zh" ? "近期作品" : "Latest Works"}
            </h2>
          </div>
          <Link href="/history">
            <Button variant="ghost" className="group gap-1.5 text-sm">
              {lang === "zh" ? "全部作品" : "View Archive"}
              <ArrowUpRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </Button>
          </Link>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {recent.map((p, i) => (
            <Link href="/workspace" key={i} className="group block">
              <div className="space-y-3 hover-lift">
                {/* Visual: editorial gradient card */}
                <div className={`relative aspect-[3/4] overflow-hidden rounded-sm bg-gradient-to-br ${p.grad} film-grain`}>
                  {/* Mock phone frame */}
                  <div className="absolute inset-x-6 inset-y-6 rounded-sm bg-white/40 dark:bg-black/40 backdrop-blur-sm border border-white/30 dark:border-white/10" />
                  <div className="absolute inset-x-8 inset-y-8 rounded-sm overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-stone-300/60 via-stone-200/60 to-amber-100/60" />
                    <div className="absolute inset-x-3 bottom-3 px-3 py-1.5 rounded bg-black/60 backdrop-blur text-[10px] text-white leading-tight">
                      {p.title.split(" ")[0]}...
                    </div>
                  </div>
                  {/* Top meta */}
                  <div className="absolute top-3 left-3 right-3 flex items-center justify-between">
                    <span className="font-display text-[9px] uppercase tracking-widest text-foreground/70">
                      №{String(i + 1).padStart(2, "0")}
                    </span>
                    <span className="font-display text-[9px] italic text-foreground/60">
                      {p.ratio} · {p.dur}
                    </span>
                  </div>
                </div>

                {/* Title */}
                <div className="space-y-0.5">
                  <h3 className="font-display text-base font-medium leading-tight editorial-underline inline-block">
                    {p.title}
                  </h3>
                  <p className="text-xs text-muted-foreground">{p.subtitle}</p>
                  <div className="flex items-center justify-between pt-1 text-[10px] text-muted-foreground/80">
                    <span>{p.segs} {lang === "zh" ? "段" : "segments"}</span>
                    <span className="italic">{p.time}</span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ========== SERVICES ========== */}
      <section className="grid gap-8 lg:grid-cols-2 animate-fade-up" style={{ animationDelay: "0.2s" }}>
        <div className="space-y-6">
          <div>
            <p className="font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Service Status</p>
            <h2 className="font-display text-3xl font-medium tracking-tight mt-1">
              {lang === "zh" ? "服務健康" : "Connected Services"}
            </h2>
            <p className="text-sm text-muted-foreground mt-1 max-w-md">
              {lang === "zh" ? "VidiForge 透過 5 個服務串聯你的工作流。" : "Five services weave the workflow together."}
            </p>
          </div>

          <div className="space-y-0 divide-y divide-border/60 border-y border-border/60">
            {services.map((s) => (
              <div key={s.name} className="flex items-center justify-between py-3.5 group">
                <div className="flex items-center gap-4">
                  <div className="font-display text-xs italic tabular-nums text-muted-foreground/60 w-6">
                    {String(services.indexOf(s) + 1).padStart(2, "0")}
                  </div>
                  <div>
                    <div className="font-display text-base font-medium">{s.name}</div>
                    <div className="text-xs text-muted-foreground">{s.role}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {s.status === "ok" ? (
                    <>
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      <span className="text-xs text-muted-foreground">{lang === "zh" ? "已連接" : "Connected"}</span>
                    </>
                  ) : (
                    <>
                      <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                      <span className="text-xs text-muted-foreground">{lang === "zh" ? "未配置" : "Missing"}</span>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>

          <Link href="/settings" className="inline-block">
            <Button variant="outline" className="rounded-full px-5">
              {lang === "zh" ? "管理服務" : "Manage Services"}
              <ArrowRight className="ml-2 h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>

        {/* Editorial pull-quote */}
        <div className="relative rounded-sm border border-border/60 bg-card/40 p-10 lg:p-12">
          <span className="absolute top-6 left-8 font-display text-7xl italic text-primary/20 leading-none">"</span>
          <blockquote className="font-display text-2xl lg:text-3xl italic leading-snug text-foreground/85 mt-4">
            {lang === "zh"
              ? "讓創作回到內容本身。讓工具回到工藝本身。"
              : "Let the making return to the work itself. Let the tools return to craft."}
          </blockquote>
          <p className="mt-6 font-display text-sm italic text-muted-foreground">
            — {lang === "zh" ? "VidiForge 宣言" : "VidiForge Manifesto"}
          </p>
          <div className="mt-8 pt-6 border-t border-border/60 flex items-center gap-3 text-xs text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span>{lang === "zh" ? "今天已為你節省 4.2 小時" : "4.2 hours saved for you today"}</span>
          </div>
        </div>
      </section>
    </div>
  );
}