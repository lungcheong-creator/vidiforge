"use client";

import { Moon, Sun, Languages, Search, Command } from "lucide-react";
import { useTheme } from "@/components/theme-provider";
import { useLang } from "@/lib/i18n";
import { Button } from "@/components/ui/button";

export function Topbar() {
  const { theme, setTheme } = useTheme();
  const { lang, setLang } = useLang();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border/60 bg-background/85 px-6 backdrop-blur-lg">
      <div className="flex flex-1 items-center gap-4">
        <div className="hidden lg:flex items-baseline gap-2">
          <span className="font-display text-xs italic text-muted-foreground">Atelier</span>
          <span className="font-display text-sm font-medium">Today</span>
          <span className="text-xs text-muted-foreground">·</span>
          <span className="text-xs text-muted-foreground tabular-nums">
            {new Date().toLocaleDateString(lang === "zh" ? "zh-CN" : "en-US", { month: "short", day: "numeric", year: "numeric" })}
          </span>
        </div>

        <div className="relative hidden md:flex w-full max-w-md ml-auto">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            placeholder={lang === "zh" ? "搜索項目、模板、設置…" : "Search projects, templates, settings…"}
            className="h-9 w-full rounded-full border border-border/80 bg-secondary/40 pl-9 pr-14 text-xs placeholder:text-muted-foreground/70 focus:outline-none focus:border-primary/50 focus:bg-background transition-colors"
          />
          <kbd className="absolute right-3 top-1/2 -translate-y-1/2 inline-flex h-5 select-none items-center rounded border border-border bg-background px-1.5 font-mono text-[10px] text-muted-foreground">
            <Command className="h-2.5 w-2.5 mr-0.5" />K
          </kbd>
        </div>
      </div>

      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setLang(lang === "zh" ? "en" : "zh")}
          className="gap-1.5 text-xs font-medium px-3"
        >
          <Languages className="h-3.5 w-3.5" />
          {lang === "zh" ? "EN" : "中文"}
        </Button>
        <div className="h-5 w-px bg-border" />
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "light" ? "dark" : "light")}
          className="h-9 w-9 rounded-full"
        >
          {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </Button>
      </div>
    </header>
  );
}