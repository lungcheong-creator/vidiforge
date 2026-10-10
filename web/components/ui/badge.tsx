"use client";

import { cn } from "@/lib/utils";

export function Badge({
  className,
  variant = "default",
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { variant?: "default" | "secondary" | "outline" | "success" | "warning" | "destructive" }) {
  const variants = {
    default: "border-transparent bg-primary text-primary-foreground",
    secondary: "border-transparent bg-secondary text-secondary-foreground",
    outline: "text-foreground",
    success: "border-transparent bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
    warning: "border-transparent bg-amber-500/15 text-amber-600 dark:text-amber-400",
    destructive: "border-transparent bg-destructive/15 text-destructive",
  };
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium transition-colors",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}