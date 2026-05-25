"use client";

import {
  Boxes,
  Code2,
  FileCode2,
  FileText,
  GitBranch,
  ListChecks,
  ShieldAlert,
} from "lucide-react";
import * as React from "react";

import { Markdown } from "@/components/app/markdown";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/misc";
import { agentMeta } from "@/lib/agents";
import { api } from "@/lib/api";
import type { ArtifactKind, ArtifactRead } from "@/lib/types";
import { cn } from "@/lib/utils";

const KIND_ICON: Record<ArtifactKind, React.ComponentType<{ className?: string }>> = {
  document: FileText,
  code: FileCode2,
  diagram: GitBranch,
  plan: ListChecks,
  report: ShieldAlert,
};

export function ArtifactExplorer({ runId, refreshKey }: { runId: string; refreshKey: number }) {
  const [artifacts, setArtifacts] = React.useState<ArtifactRead[] | null>(null);
  const [selected, setSelected] = React.useState<string | null>(null);

  React.useEffect(() => {
    api
      .listArtifacts(runId)
      .then((arts) => {
        setArtifacts(arts);
        setSelected((cur) => cur ?? arts[0]?.id ?? null);
      })
      .catch(() => setArtifacts([]));
  }, [runId, refreshKey]);

  if (artifacts === null) {
    return (
      <div className="grid gap-4 md:grid-cols-[260px_1fr]">
        <Skeleton className="h-[400px]" />
        <Skeleton className="h-[400px]" />
      </div>
    );
  }

  if (artifacts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-16 text-center text-sm text-muted-foreground">
        <Boxes className="mb-3 h-8 w-8" />
        Artifacts will appear here as the team produces them.
      </div>
    );
  }

  const current = artifacts.find((a) => a.id === selected) ?? artifacts[0];

  return (
    <div className="grid gap-4 md:grid-cols-[280px_1fr]">
      {/* File list */}
      <div className="scrollbar-thin max-h-[600px] space-y-0.5 overflow-y-auto rounded-xl border border-border/60 bg-card/40 p-2">
        {artifacts.map((a) => {
          const Icon = KIND_ICON[a.kind] ?? FileText;
          const meta = agentMeta(a.produced_by);
          const active = a.id === current.id;
          return (
            <button
              key={a.id}
              onClick={() => setSelected(a.id)}
              className={cn(
                "flex w-full items-start gap-2 rounded-lg px-2.5 py-2 text-left transition-colors",
                active ? "bg-secondary" : "hover:bg-secondary/50",
              )}
            >
              <Icon className={cn("mt-0.5 h-4 w-4 shrink-0", active ? "text-primary" : "text-muted-foreground")} />
              <div className="min-w-0 flex-1">
                <div className="truncate text-xs font-medium">{a.title}</div>
                <div className="truncate font-mono text-[10px] text-muted-foreground">{a.path}</div>
              </div>
              <span className={cn("mt-1 h-1.5 w-1.5 shrink-0 rounded-full", meta.dot)} />
            </button>
          );
        })}
      </div>

      {/* Viewer */}
      <div className="scrollbar-thin max-h-[600px] overflow-y-auto rounded-xl border border-border/60 bg-card/40 p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <Code2 className="h-4 w-4 text-muted-foreground" />
              <span className="font-mono text-sm">{current.path}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="capitalize">
              {current.kind}
            </Badge>
            <Badge variant="secondary">{agentMeta(current.produced_by).label}</Badge>
          </div>
        </div>

        <ArtifactBody artifact={current} />
      </div>
    </div>
  );
}

function ArtifactBody({ artifact }: { artifact: ArtifactRead }) {
  if (artifact.kind === "code") {
    return (
      <pre className="scrollbar-thin overflow-x-auto rounded-lg border border-border/60 bg-[hsl(var(--muted))]/40 p-4 font-mono text-[13px] leading-relaxed">
        <code>{artifact.content}</code>
      </pre>
    );
  }
  return <Markdown content={artifact.content} />;
}
