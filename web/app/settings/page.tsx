"use client";

import { useEffect, useState } from "react";
import { useLang } from "@/lib/i18n";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Key, Lock, Eye, EyeOff, Check, Shield, HardDrive, Info, ExternalLink, Github, Heart, RefreshCw, AlertCircle } from "lucide-react";
import { listKeys, saveKey, listLLMProviders, deleteKey, getHealth } from "@/lib/api";
import { Input } from "@/components/ui/input";
import type { ApiKeyEntry as ApiKeyEntryType } from "@/lib/api-types";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const { t, lang } = useLang();
  const [tab, setTab] = useState<"keys" | "prefs" | "storage" | "about">("keys");
  const [showKey, setShowKey] = useState(false);
  const [entries, setEntries] = useState<ApiKeyEntryType[]>([]);
  const [providers, setProviders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [apiUrl, setApiUrl] = useState<string>("");

  useEffect(() => {
    refresh();
    getHealth()
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false));
    if (typeof window !== "undefined") {
      setApiUrl((window as any).__VIDIFORGE_API_URL__ || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080");
    }
  }, []);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const [keys, llms] = await Promise.all([listKeys(), listLLMProviders()]);
      setEntries(keys);
      setProviders(llms);
    } catch (e: any) {
      setError(e.message || "Failed to load settings");
    } finally {
      setLoading(false);
    }
  }

  async function handleSave(provider: string) {
    if (!editValue.trim()) return;
    try {
      await saveKey(provider, editValue.trim());
      setEditing(null);
      setEditValue("");
      await refresh();
    } catch (e: any) {
      setError(e.message || "Failed to save key");
    }
  }

  async function handleDelete(provider: string) {
    if (!confirm(lang === "zh" ? `刪除 ${provider} 密鑰？` : `Delete ${provider} key?`)) return;
    try {
      await deleteKey(provider);
      await refresh();
    } catch (e: any) {
      setError(e.message || "Failed to delete key");
    }
  }

  const tabs = [
    { k: "keys", l: t("set_tab_keys"), icon: Key },
    { k: "prefs", l: t("set_tab_prefs"), icon: Shield },
    { k: "storage", l: t("set_tab_storage"), icon: HardDrive },
    { k: "about", l: t("set_tab_about"), icon: Info },
  ];

  return (
    <div className="mx-auto max-w-6xl px-6 py-10 lg:px-12 lg:py-14 space-y-8 animate-fade-up">
      <header className="space-y-3">
        <div className="flex items-center gap-3 text-xs uppercase tracking-[0.2em] text-muted-foreground">
          <span className="font-display italic">Atelier</span>
          <span className="h-px w-12 bg-border" />
          <span className="tabular-nums">No. 007</span>
          <span className="font-display italic">Settings</span>
        </div>
        <h1 className="font-display text-5xl font-medium tracking-tight lg:text-6xl">
          {t("set_title")}<span className="italic text-primary">.</span>
        </h1>
        <p className="font-display italic text-muted-foreground">
          {lang === "zh" ? "管理 API 密鑰、偏好、存儲策略。" : "Manage API keys, preferences, and storage."}
        </p>
      </header>

      {/* API status banner */}
      <Card className="border-border/60 bg-card/60 p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn(
              "h-2 w-2 rounded-full",
              apiOnline === true ? "bg-emerald-500 animate-pulse" :
              apiOnline === false ? "bg-destructive" : "bg-muted-foreground/40"
            )} />
            <div>
              <div className="font-display text-sm font-medium">
                {apiOnline === true ? "API Connected" : apiOnline === false ? "API Offline" : "Checking..."}
              </div>
              <div className="text-xs font-mono text-muted-foreground">{apiUrl}</div>
            </div>
          </div>
          <Button variant="ghost" size="sm" className="gap-1.5 rounded-full" onClick={refresh}>
            <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin")} />
            {lang === "zh" ? "刷新" : "Refresh"}
          </Button>
        </div>
      </Card>

      <div className="grid gap-8 lg:grid-cols-[200px_1fr]">
        {/* Side tabs */}
        <div className="space-y-1">
          {tabs.map(tb => {
            const Icon = tb.icon;
            const active = tab === tb.k;
            return (
              <button
                key={tb.k}
                onClick={() => setTab(tb.k as typeof tab)}
                className={cn(
                  "w-full flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors font-medium",
                  active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{tb.l}</span>
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="space-y-4">
          {tab === "keys" && (
            <Card className="border-border/60 bg-card/60 backdrop-blur">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Key className="h-4 w-4 text-primary" />
                  {t("set_tab_keys")}
                </CardTitle>
                <CardDescription>{t("set_keys_desc")}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {error && (
                  <div className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm">
                    <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
                    <span className="text-destructive">{error}</span>
                  </div>
                )}

                {loading && entries.length === 0 ? (
                  <div className="text-sm text-muted-foreground py-8 text-center">{lang === "zh" ? "加載中…" : "Loading…"}</div>
                ) : providers.length === 0 ? (
                  <div className="text-sm text-muted-foreground py-8 text-center">
                    {lang === "zh" ? "無法連接 API。請檢查 API 是否運行。" : "Cannot reach API. Is it running?"}
                  </div>
                ) : (
                  providers.map((p) => {
                    const stored = entries.find(e => e.provider === p.id);
                    const isEditing = editing === p.id;
                    return (
                      <div key={p.id} className="flex items-center gap-3 rounded-sm border border-border/60 bg-card p-3">
                        <div className={cn(
                          "flex h-9 w-9 items-center justify-center rounded-full",
                          stored?.has_value ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                        )}>
                          <Key className="h-4 w-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-display text-sm font-medium">{p.name}</span>
                            {p.active && <Badge variant="default" className="text-[9px] rounded-full">active</Badge>}
                            {stored?.has_value && <Badge variant="success" className="text-[9px] rounded-full">stored</Badge>}
                          </div>
                          <div className="text-xs text-muted-foreground font-mono">
                            {p.default_model} · {p.id}
                          </div>
                        </div>
                        {isEditing ? (
                          <>
                            <Input
                              type={showKey ? "text" : "password"}
                              autoFocus
                              placeholder={p.id}
                              value={editValue}
                              onChange={e => setEditValue(e.target.value)}
                              onKeyDown={e => {
                                if (e.key === "Enter") handleSave(p.id);
                                if (e.key === "Escape") { setEditing(null); setEditValue(""); }
                              }}
                              className="max-w-[260px] font-mono text-xs"
                            />
                            <Button size="sm" className="rounded-full" onClick={() => handleSave(p.id)}>
                              <Check className="h-3.5 w-3.5" />
                            </Button>
                            <Button size="sm" variant="ghost" className="rounded-full" onClick={() => { setEditing(null); setEditValue(""); }}>
                              {lang === "zh" ? "取消" : "Cancel"}
                            </Button>
                          </>
                        ) : (
                          <>
                            <code className="font-mono text-xs text-muted-foreground max-w-[180px] truncate">
                              {stored?.masked || (lang === "zh" ? "未設置" : "Not set")}
                            </code>
                            <Button size="sm" variant="outline" className="rounded-full" onClick={() => { setEditing(p.id); setEditValue(""); }}>
                              {stored?.has_value ? (lang === "zh" ? "替換" : "Replace") : (lang === "zh" ? "設置" : "Set")}
                            </Button>
                            {stored?.has_value && (
                              <Button size="sm" variant="ghost" className="rounded-full" onClick={() => handleDelete(p.id)}>
                                {lang === "zh" ? "刪除" : "Delete"}
                              </Button>
                            )}
                            <Button variant="ghost" size="icon" onClick={() => setShowKey(!showKey)} className="h-8 w-8 rounded-full">
                              {showKey ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                            </Button>
                          </>
                        )}
                      </div>
                    );
                  })
                )}
              </CardContent>
            </Card>
          )}

          {tab === "prefs" && (
            <Card className="border-border/60 bg-card/60">
              <CardHeader>
                <CardTitle>{t("set_tab_prefs")}</CardTitle>
                <CardDescription>{lang === "zh" ? "個人偏好（本地存儲）" : "Personal preferences (local storage)"}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <PrefRow label={lang === "zh" ? "默認畫幅" : "Default aspect"} value="9:16" />
                <PrefRow label={lang === "zh" ? "默認配音" : "Default TTS"} value="Edge TTS · 曉曉" />
                <PrefRow label={lang === "zh" ? "字幕位置" : "Subtitle position"} value={lang === "zh" ? "底部" : "Bottom"} />
                <PrefRow label={lang === "zh" ? "默認素材庫" : "Default source"} value="Pexels" />
                <PrefRow label={lang === "zh" ? "暗色模式" : "Dark mode"} value={lang === "zh" ? "跟隨系統" : "System"} switch />
                <PrefRow label={lang === "zh" ? "完成後通知" : "Notifications"} value={lang === "zh" ? "開啟" : "On"} switch on />
                <PrefRow label={lang === "zh" ? "自動保存草稿" : "Auto-save drafts"} value={lang === "zh" ? "每 30 秒" : "Every 30s"} switch on />
                <p className="text-xs text-muted-foreground pt-2">
                  {lang === "zh" ? "偏好設置保存在瀏覽器 localStorage。" : "Preferences are stored in browser localStorage."}
                </p>
              </CardContent>
            </Card>
          )}

          {tab === "storage" && (
            <Card className="border-border/60 bg-card/60">
              <CardHeader>
                <CardTitle>{t("set_tab_storage")}</CardTitle>
                <CardDescription>{lang === "zh" ? "輸出視頻與緩存。" : "Outputs and cache."}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <StorageRow icon={HardDrive} label={t("set_storage_local")} value="2.3 GB / 10 GB" percent={23} gradient="from-violet-500 to-indigo-600" />
                <StorageRow icon={Info} label={t("set_storage_cloud") + " (R2)"} value="12.7 GB / 100 GB" percent={13} gradient="from-cyan-500 to-blue-600" />
                <p className="text-xs text-muted-foreground">
                  {lang === "zh" ? "存儲統計由 API 端 SQLite 與 Railway 卷提供。" : "Storage stats from API SQLite + Railway volumes."}
                </p>
              </CardContent>
            </Card>
          )}

          {tab === "about" && (
            <Card className="border-border/60 bg-card/60">
              <CardHeader>
                <CardTitle>{t("set_tab_about")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4 pb-4 border-b border-border/60">
                  <div className="flex h-12 w-12 items-center justify-center rounded-md bg-gradient-to-br from-violet-500 to-indigo-600 text-white font-bold text-xl">
                    V
                  </div>
                  <div>
                    <div className="text-base font-semibold">VidiForge · 智選銀河</div>
                    <div className="text-xs text-muted-foreground mt-0.5">v0.1.0 · 2026-10-09</div>
                  </div>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <a href="https://github.com/harry0703/MoneyPrinterTurbo" target="_blank" rel="noopener" className="flex items-center justify-between rounded-sm border p-3 hover:bg-accent transition-colors">
                    <div className="flex items-center gap-2">
                      <Github className="h-4 w-4" />
                      <div className="text-sm font-medium">MoneyPrinterTurbo</div>
                    </div>
                    <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
                  </a>
                  <div className="flex items-center justify-between rounded-sm border p-3">
                    <div className="flex items-center gap-2">
                      <Heart className="h-4 w-4 text-rose-400" />
                      <div className="text-sm font-medium">{lang === "zh" ? "由 Michael 構建" : "Built by Michael"}</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function PrefRow({ label, value, switch: isSwitch, on }: { label: string; value: string; switch?: boolean; on?: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-sm border border-border/60 bg-card p-3">
      <span className="text-sm font-display">{label}</span>
      {isSwitch ? (
        <div className={cn("h-5 w-9 rounded-full relative transition-colors cursor-pointer", on ? "bg-primary" : "bg-muted")}>
          <div className={cn("absolute top-0.5 h-4 w-4 rounded-full bg-white transition-all shadow", on ? "left-4" : "left-0.5")} />
        </div>
      ) : (
        <span className="text-sm text-muted-foreground font-display italic">{value}</span>
      )}
    </div>
  );
}

function StorageRow({ icon: Icon, label, value, percent, gradient }: any) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-sm font-display">
          <Icon className="h-4 w-4 text-primary" />
          {label}
        </div>
        <div className="text-xs text-muted-foreground tabular-nums font-display">{value}</div>
      </div>
      <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
        <div className={cn("h-full rounded-full bg-gradient-to-r", gradient)} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}