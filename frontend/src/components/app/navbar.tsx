import { Github, Network } from "lucide-react";
import Link from "next/link";

import { ThemeToggle } from "@/components/app/theme";
import { Badge } from "@/components/ui/badge";

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/60 bg-background/80 backdrop-blur-xl">
      <div className="container flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-fuchsia-500 shadow-lg shadow-primary/30">
            <Network className="h-5 w-5 text-white" />
          </div>
          <div className="leading-tight">
            <div className="text-sm font-semibold">AI Engineering Team</div>
            <div className="text-[11px] text-muted-foreground">
              Multi-agent software engineering, orchestrated
            </div>
          </div>
        </Link>

        <div className="flex items-center gap-2">
          <Badge variant="outline" className="hidden sm:inline-flex">
            <span className="mr-1 h-1.5 w-1.5 rounded-full bg-[hsl(var(--success))]" />
            LangGraph
          </Badge>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary/60 hover:text-foreground"
            aria-label="GitHub"
          >
            <Github className="h-4 w-4" />
          </a>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
