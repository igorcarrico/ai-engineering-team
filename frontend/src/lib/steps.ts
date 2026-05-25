import { AGENT_SEQUENCE } from "./agents";
import type { AgentKey, RunEvent, StepStatus } from "./types";

export interface LiveStep {
  agent: AgentKey;
  status: StepStatus;
  durationMs: number | null;
  retries: number;
  iteration: number;
}

/** Reconstruct per-agent step status from the event stream (client mirror of the backend). */
export function deriveSteps(events: RunEvent[]): LiveStep[] {
  const byAgent = new Map<AgentKey, RunEvent[]>();
  for (const e of events) {
    if (e.agent && (AGENT_SEQUENCE as string[]).includes(e.agent)) {
      const list = byAgent.get(e.agent) ?? [];
      list.push(e);
      byAgent.set(e.agent, list);
    }
  }

  return AGENT_SEQUENCE.map((agent) => {
    const evs = byAgent.get(agent) ?? [];
    const started = evs.filter((e) => e.type === "agent_started");
    const completed = evs.filter((e) => e.type === "agent_completed");
    const failed = evs.filter((e) => e.type === "agent_failed");
    const retries = evs.filter((e) => e.type === "agent_retry").length;
    const iteration = evs.reduce((m, e) => Math.max(m, e.iteration), 0);

    let status: StepStatus = "pending";
    if (failed.length && (!completed.length || true)) status = "failed";
    if (completed.length) status = "completed";
    else if (started.length) status = "running";
    if (failed.length && !completed.length) status = "failed";

    const durationMs =
      completed.length > 0
        ? ((completed[completed.length - 1].data?.duration_ms as number) ?? null)
        : null;

    return { agent, status, durationMs, retries, iteration };
  });
}

export function overallProgress(steps: LiveStep[], finished: boolean): number {
  if (finished) return 100;
  const done = steps.filter((s) => s.status === "completed").length;
  const running = steps.some((s) => s.status === "running") ? 0.5 : 0;
  return Math.round(((done + running) / steps.length) * 100);
}
