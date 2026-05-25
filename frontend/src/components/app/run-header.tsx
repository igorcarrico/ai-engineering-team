"use client";

import { ArrowLeft, Clock, Cpu, Gauge, Loader2, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";

import { ExportMenu } from "@/components/app/export-menu";
import { StatusBadge } from "@/components/app/status-badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/misc";
import { api } from "@/lib/api";
import type { RunDetail, RunStatus } from "@/lib/types";
import { formatDuration } from "@/lib/utils";

interface Props {
  detail: RunDetail;
  status: RunStatus;
  progress: number;
  score: number | null;
  durationMs: number | null;
  iteration: number;
  finished: boolean;
}

export function RunHeader({ detail, status, progress, score, durationMs, iteration, finished }: Props) {
  const router = useRouter();
  const [rerunning, setRerunning] = React.useState(false);
  const { project, run } = detail;

  async function rerun() {
    setRerunning(true);
    try {
      const next = await api.rerunProject(project.id);
      router.push(`/runs/${next.run.id}`);
    } finally {
      setRerunning(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> All runs
        </Link>
        <div className="flex items-center gap-2">
          <ExportMenu runId={run.id} disabled={!finished} />
          <Button variant="outline" size="sm" onClick={rerun} disabled={rerunning}>
            {rerunning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
            Re-run
          </Button>
        </div>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            <h1 className="truncate text-2xl font-bold tracking-tight">{project.name}</h1>
            <StatusBadge status={status} />
          </div>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{project.idea}</p>
        </div>
      </div>

      {/* Stat strip */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat icon={Cpu} label="Provider" value={`${run.provider} · ${run.model}`} mono />
        <Stat icon={Gauge} label="Quality score" value={score != null ? `${score}/100` : "—"} />
        <Stat icon={Clock} label="Duration" value={formatDuration(durationMs)} />
        <Stat icon={RefreshCw} label="Iteration" value={`${iteration + 1} / ${run.max_iterations}`} />
      </div>

      {!finished && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Workflow progress</span>
            <span>{progress}%</span>
          </div>
          <Progress value={progress} />
        </div>
      )}
    </div>
  );
}

function Stat({
  icon: Icon,
  label,
  value,
  mono,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded-lg border border-border/60 bg-card/40 px-3 py-2.5">
      <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
        <Icon className="h-3 w-3" />
        {label}
      </div>
      <div className={`mt-0.5 truncate text-sm font-semibold ${mono ? "font-mono text-xs" : ""}`}>
        {value}
      </div>
    </div>
  );
}
