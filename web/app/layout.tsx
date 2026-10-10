import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { LanguageProvider } from "@/lib/i18n";
import { Sidebar } from "@/components/sidebar";
import { Topbar } from "@/components/topbar";
import { TokenGate } from "@/components/token-gate";

export const metadata: Metadata = {
  title: "VidiForge · AI Video Studio",
  description: "智選銀河 · 從一個想法到一段成片",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,600;0,9..144,700;1,9..144,400;1,9..144,500&family=Inter:wght@400;500;600;700&family=Noto+Serif+SC:wght@500;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-background font-sans">
        <ThemeProvider>
          <LanguageProvider>
            <TokenGate>
              <div className="flex min-h-screen bg-editorial">
                <Sidebar />
                <div className="flex flex-1 flex-col min-w-0">
                  <Topbar />
                  <main className="flex-1 overflow-y-auto">{children}</main>
                </div>
              </div>
            </TokenGate>
          </LanguageProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}