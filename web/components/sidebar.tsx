"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Wand2, FolderOpen, ListTodo, History,
  Sparkles, Settings, Plus,
} from "lucide-react";
import { useLang } from "@/lib/i18n";
import { cn } from "@/lib/utils";

const items = [
  { key: "nav_dashboard", href: "/", icon: LayoutDashboard, num: "01" },
  { key: "nav_create", href: "/create", icon: Wand2, num: "02" },
  { key: "nav_workspace", href: "/workspace", icon: FolderOpen, num: "03" },
  { key: "nav_batch", href: "/batch", icon: ListTodo, num: "04" },
  { key: "nav_history", href: "/history", icon: History, num: "05" },
  { key: "nav_agent", href: "/agent", icon: Sparkles, num: "06" },
  { key: "nav_settings", href: "/settings", icon: Settings, num: "07" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { t } = useLang();

  return (
    <aside className="hidden lg:flex w-64 shrink-0 flex-col border-r border-border/60 bg-background">
      {/* Logo */}
      <Link href="/" className="flex items-baseline gap-2 px-6 pt-7 pb-2">
        <span className="font-display text-2xl font-semibold tracking-tight text-foreground">VidiForge</span>
        <span className="font-display text-[10px] italic text-muted-foreground">est. 2026</span>
      </Link>
      <p className="px-6 pb-6 font-display text-xs italic text-muted-foreground">
        {t("brand").split(" ").slice(1).join(" ") || "AI Video Atelier"}
      </p>

      <div className="border-t border-border/40" />

      {/* Section label */}
      <div className="px-6 pt-6 pb-3 text-[10px] uppercase tracking-[0.18em] text-muted-foreground/70">
        {t("dash_subtitle") ? "Atelier" : "Atelier"} · Menu
      </div>

      <nav className="flex-1 space-y-0.5 px-3">
        {items.map((item) => {
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group relative flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-all duration-300",
                active
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-foreground/70 hover:text-foreground hover:bg-secondary/50"
              )}
            >
              <span className={cn(
                "font-display text-[10px] tabular-nums tracking-wider",
                active ? "text-primary-foreground/70" : "text-muted-foreground/60"
              )}>
                {item.num}
              </span>
              <Icon className="h-4 w-4 shrink-0" />
              <span className="font-medium">{t(item.key)}</span>
              {active && (
                <span className="absolute right-3 h-1.5 w-1.5 rounded-full bg-primary-foreground animate-pulse" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="border-t border-border/40 px-6 py-5 space-y-4">
        <div>
          <p className="font-display text-sm italic leading-snug text-foreground/80">
            "Every reel begins as a single thought."
          </p>
          <p className="mt-1 text-[10px] uppercase tracking-widest text-muted-foreground/60">— VidiForge Manifesto</p>
        </div>
        <button className="flex w-full items-center justify-between rounded-md border border-border/80 px-3 py-2 text-xs text-muted-foreground hover:border-primary hover:text-primary transition-colors">
          <span>New Project</span>
          <Plus className="h-3.5 w-3.5" />
        </button>
      </div>
    </aside>
  );
}