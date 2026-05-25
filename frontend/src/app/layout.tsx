import type { Metadata } from "next";

import { Navbar } from "@/components/app/navbar";
import { ThemeProvider } from "@/components/app/theme";

import "./globals.css";

export const metadata: Metadata = {
  title: "AI Engineering Team — autonomous multi-agent software engineering",
  description:
    "A team of specialized AI agents — PM, Architect, Engineers, QA, Security and Reviewer — collaborate via a LangGraph workflow to turn an idea into a structured engineering plan.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen font-sans">
        <ThemeProvider>
          <div className="relative flex min-h-screen flex-col">
            <Navbar />
            <main className="flex-1">{children}</main>
            <footer className="border-t border-border/60 py-6">
              <div className="container flex flex-col items-center justify-between gap-2 text-xs text-muted-foreground sm:flex-row">
                <span>
                  Built with FastAPI · LangGraph · Next.js — a reference multi-agent architecture.
                </span>
                <span>Runs in mock mode with zero API keys.</span>
              </div>
            </footer>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
