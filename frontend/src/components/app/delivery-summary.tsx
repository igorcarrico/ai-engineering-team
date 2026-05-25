"use client";

import { CheckCircle2, Loader2 } from "lucide-react";

import { Markdown } from "@/components/app/markdown";
import { Badge } from "@/components/ui/badge";
import type { RunDetail } from "@/lib/types";

export function DeliverySummary({ detail, finished }: { detail: RunDetail; finished: boolean }) {
  const { run, outputs } = detail;
  const review = (outputs?.code_reviewer ?? {}) as Record<string, any>;
  const pm = (outputs?.product_manager ?? {}) as Record<string, any>;

  if (!finished || !run.final_summary) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-16 text-center text-sm text-muted-foreground">
        <Loader2 className="mb-3 h-6 w-6 animate-spin" />
        The delivery summary will be ready once the review completes.
      </div>
    );
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_280px]">
      <div className="rounded-xl border border-border/60 bg-card/40 p-6">
        <Markdown content={run.final_summary} />
      </div>

      <aside className="space-y-4">
        <div className="flex flex-col items-center rounded-xl border border-border/60 bg-card/40 p-6">
          <ScoreRing score={run.review_score ?? 0} />
          <Badge variant={review.verdict === "approve" ? "success" : "warning"} className="mt-3">
            <CheckCircle2 className="h-3 w-3" />
            {String(review.verdict ?? "n/a").toUpperCase()}
          </Badge>
          <p className="mt-2 text-center text-xs text-muted-foreground">Engineering quality score</p>
        </div>

        {Array.isArray(pm.success_metrics) && pm.success_metrics.length > 0 && (
          <div className="rounded-xl border border-border/60 bg-card/40 p-5">
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Success metrics
            </h4>
            <ul className="space-y-1.5 text-xs text-muted-foreground">
              {pm.success_metrics.slice(0, 4).map((m: string, i: number) => (
                <li key={i} className="flex gap-2">
                  <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-primary" />
                  {m}
                </li>
              ))}
            </ul>
          </div>
        )}
      </aside>
    </div>
  );
}

function ScoreRing({ score }: { score: number }) {
  const r = 42;
  const c = 2 * Math.PI * r;
  const offset = c - (score / 100) * c;
  return (
    <div className="relative h-28 w-28">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={r} fill="none" stroke="hsl(var(--border))" strokeWidth="8" />
        <circle
          cx="50"
          cy="50"
          r={r}
          fill="none"
          stroke="hsl(var(--primary))"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          className="transition-all duration-1000"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold">{score}</span>
        <span className="text-[10px] text-muted-foreground">/ 100</span>
      </div>
    </div>
  );
}
