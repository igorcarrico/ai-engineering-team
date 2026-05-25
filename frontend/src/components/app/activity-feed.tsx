"use client";

import {
  CheckCircle2,
  FileText,
  Loader2,
  Play,
  RefreshCw,
  Rocket,
  XCircle,
} from "lucide-react";
import * as React from "react";

import { agentMeta } from "@/lib/agents";
import type { EventType, RunEvent } from "@/lib/types";
import { cn, timeOfDay } from "@/lib/utils";

const ICON: Partial<Record<EventType, React.ComponentType<{ className?: string }>>> = {
  run_started: Rocket,
  agent_started: Play,
  agent_completed: CheckCircle2,
  agent_failed: XCircle,
  agent_retry: RefreshCw,
  artifact_created: FileText,
  iteration_started: RefreshCw,
  run_completed: CheckCircle2,
  run_failed: XCircle,
};

export function ActivityFeed({ events, live }: { events: RunEvent[]; live: boolean }) {
  const bottomRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [events.length]);

  return (
    <div className="scrollbar-thin max-h-[560px] space-y-1 overflow-y-auto pr-1 font-mono text-[13px]">
      {events.length === 0 && (
        <div className="flex items-center gap-2 py-8 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> Waiting for the team to start…
        </div>
      )}
      {events.map((e) => {
        const meta = agentMeta(e.agent);
        const Icon = ICON[e.type] ?? Play;
        const isProgress = e.type === "agent_progress";
        return (
          <div
            key={e.id}
            className={cn(
              "flex items-start gap-2 rounded-md px-2 py-1 animate-fade-in-up",
              isProgress ? "opacity-70" : "hover:bg-secondary/30",
            )}
          >
            <span className="mt-0.5 shrink-0 text-[11px] tabular-nums text-muted-foreground/60">
              {timeOfDay(e.created_at)}
            </span>
            <Icon className={cn("mt-0.5 h-3.5 w-3.5 shrink-0", meta.text)} />
            <span className={cn("shrink-0 font-medium", meta.text)}>
              [{e.agent_label ?? "system"}]
            </span>
            <span className="text-foreground/85">{e.message}</span>
          </div>
        );
      })}
      {live && events.length > 0 && (
        <div className="flex items-center gap-2 px-2 py-1 text-[11px] text-muted-foreground">
          <span className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-[hsl(var(--success))]" />
          streaming live
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
