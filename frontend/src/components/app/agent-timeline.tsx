"use client";

import { Check, Loader2, RefreshCw, X } from "lucide-react";

import { AGENT_META } from "@/lib/agents";
import type { LiveStep } from "@/lib/steps";
import { cn, formatDuration } from "@/lib/utils";

export function AgentTimeline({ steps }: { steps: LiveStep[] }) {
  return (
    <ol className="relative space-y-1">
      {steps.map((step, i) => {
        const meta = AGENT_META[step.agent];
        const Icon = meta.icon;
        const last = i === steps.length - 1;
        return (
          <li key={step.agent} className="relative flex gap-3 pb-2">
            {!last && (
              <span
                className={cn(
                  "absolute left-[15px] top-8 h-[calc(100%-1rem)] w-px",
                  step.status === "completed" ? "bg-[hsl(var(--success))]/30" : "bg-border",
                )}
              />
            )}
            <div
              className={cn(
                "z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                meta.bg,
                step.status === "running" && "ring-2 ring-primary animate-pulse-soft",
              )}
            >
              <Icon className={cn("h-4 w-4", meta.text)} />
            </div>
            <div className="flex min-w-0 flex-1 items-center justify-between gap-2 pt-1">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-medium">{meta.label}</span>
                  {step.retries > 0 && (
                    <span className="flex items-center gap-0.5 text-[10px] text-[hsl(var(--warning))]">
                      <RefreshCw className="h-2.5 w-2.5" />
                      {step.retries}
                    </span>
                  )}
                </div>
                <span className="text-[11px] text-muted-foreground">{meta.blurb}</span>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {step.durationMs != null && step.status === "completed" && (
                  <span className="text-[11px] tabular-nums text-muted-foreground">
                    {formatDuration(step.durationMs)}
                  </span>
                )}
                <StatusDot status={step.status} />
              </div>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function StatusDot({ status }: { status: LiveStep["status"] }) {
  if (status === "completed")
    return (
      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[hsl(var(--success))]/15">
        <Check className="h-3 w-3 text-[hsl(var(--success))]" strokeWidth={3} />
      </span>
    );
  if (status === "running")
    return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
  if (status === "failed")
    return (
      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[hsl(var(--danger))]/15">
        <X className="h-3 w-3 text-[hsl(var(--danger))]" strokeWidth={3} />
      </span>
    );
  return <span className="h-2 w-2 rounded-full bg-border" />;
}
