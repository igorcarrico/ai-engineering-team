"use client";

import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";
import type { RunEvent, RunStatus } from "@/lib/types";

interface RunStreamState {
  events: RunEvent[];
  connected: boolean;
  finished: boolean;
}

/**
 * Subscribes to a run's Server-Sent Events stream.
 *
 * The backend replays the full history on connect, so this hook works whether
 * the client joins at the start of a run or long after it finished. It is the
 * single source of truth for the live activity feed and the derived timeline.
 */
export function useRunStream(runId: string, initialStatus: RunStatus) {
  const [state, setState] = useState<RunStreamState>({
    events: [],
    connected: false,
    finished: initialStatus === "completed" || initialStatus === "failed",
  });
  const seen = useRef<Set<string>>(new Set());

  useEffect(() => {
    seen.current = new Set();
    setState({ events: [], connected: false, finished: false });

    const source = new EventSource(api.streamUrl(runId));

    source.onopen = () => setState((s) => ({ ...s, connected: true }));

    source.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as RunEvent;
        if (seen.current.has(event.id)) return;
        seen.current.add(event.id);
        setState((s) => ({ ...s, events: [...s.events, event] }));
      } catch {
        /* ignore malformed frames */
      }
    };

    source.addEventListener("done", () => {
      setState((s) => ({ ...s, finished: true, connected: false }));
      source.close();
    });

    source.onerror = () => {
      // EventSource auto-reconnects; reflect the transient disconnect.
      setState((s) => ({ ...s, connected: false }));
    };

    return () => source.close();
  }, [runId]);

  return state;
}
