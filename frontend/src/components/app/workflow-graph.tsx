"use client";

import { Check, ChevronRight, Loader2, RotateCcw } from "lucide-react";

import { AGENT_META } from "@/lib/agents";
import type { AgentKey, StepStatus } from "@/lib/types";
import type { LiveStep } from "@/lib/steps";
import { cn } from "@/lib/utils";

function statusRing(status: StepStatus) {
  switch (status) {
    case "running":
      return "ring-2 ring-primary animate-pulse-soft";
    case "completed":
      return "ring-1 ring-[hsl(var(--success))]/40";
    case "failed":
      return "ring-2 ring-[hsl(var(--danger))]";
    default:
      return "ring-1 ring-border opacity-50";
  }
}

function Node({ agent, status }: { agent: AgentKey; status: StepStatus }) {
  const meta = AGENT_META[agent];
  const Icon = meta.icon;
  return (
    <div className="flex flex-col items-center gap-1.5">
      <div
        className={cn(
          "relative flex h-12 w-12 items-center justify-center rounded-xl transition-all",
          meta.bg,
          statusRing(status),
        )}
      >
        <Icon className={cn("h-5 w-5", meta.text)} />
        {status === "completed" && (
          <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-[hsl(var(--success))] text-background">
            <Check className="h-2.5 w-2.5" strokeWidth={3} />
          </span>
        )}
        {status === "running" && (
          <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-primary-foreground">
            <Loader2 className="h-2.5 w-2.5 animate-spin" />
          </span>
        )}
      </div>
      <span className="max-w-[68px] text-center text-[10px] leading-tight text-muted-foreground">
        {meta.short}
      </span>
    </div>
  );
}

const Arrow = () => <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground/40" />;

export function WorkflowGraph({ steps }: { steps: LiveStep[] }) {
  const byKey = Object.fromEntries(steps.map((s) => [s.agent, s])) as Record<AgentKey, LiveStep>;
  const st = (k: AgentKey) => byKey[k]?.status ?? "pending";
  const refining = byKey.architect?.iteration > 0 || (byKey.code_reviewer?.iteration ?? 0) > 0;

  return (
    <div className="scrollbar-thin overflow-x-auto">
      <div className="flex min-w-max items-center gap-2 py-2">
        <Node agent="product_manager" status={st("product_manager")} />
        <Arrow />
        <Node agent="architect" status={st("architect")} />
        <Arrow />
        {/* parallel branch */}
        <div className="flex flex-col gap-2 rounded-xl border border-dashed border-border/50 px-2 py-1.5">
          <span className="text-center text-[9px] uppercase tracking-wider text-muted-foreground/60">
            parallel
          </span>
          <div className="flex gap-3">
            <Node agent="backend_engineer" status={st("backend_engineer")} />
            <Node agent="frontend_engineer" status={st("frontend_engineer")} />
          </div>
        </div>
        <Arrow />
        <Node agent="qa_engineer" status={st("qa_engineer")} />
        <Arrow />
        <Node agent="security_reviewer" status={st("security_reviewer")} />
        <Arrow />
        <Node agent="code_reviewer" status={st("code_reviewer")} />
      </div>

      <div
        className={cn(
          "mt-1 flex items-center gap-1.5 text-[11px] transition-opacity",
          refining ? "text-primary opacity-100" : "text-muted-foreground/50 opacity-70",
        )}
      >
        <RotateCcw className="h-3 w-3" />
        Conditional refine loop: reviewer → architect{refining ? " (engaged)" : ""}
      </div>
    </div>
  );
}
