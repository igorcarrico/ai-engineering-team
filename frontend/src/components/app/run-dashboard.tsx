"use client";

import { Activity, FolderTree, Sparkles } from "lucide-react";
import * as React from "react";

import { ActivityFeed } from "@/components/app/activity-feed";
import { AgentTimeline } from "@/components/app/agent-timeline";
import { ArtifactExplorer } from "@/components/app/artifact-explorer";
import { DeliverySummary } from "@/components/app/delivery-summary";
import { RunHeader } from "@/components/app/run-header";
import { WorkflowGraph } from "@/components/app/workflow-graph";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/misc";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useRunStream } from "@/hooks/useRunStream";
import { api } from "@/lib/api";
import { deriveSteps, overallProgress } from "@/lib/steps";
import type { RunDetail, RunStatus } from "@/lib/types";

export function RunDashboard({ runId }: { runId: string }) {
  const [detail, setDetail] = React.useState<RunDetail | null>(null);
  const [refreshKey, setRefreshKey] = React.useState(0);
  const [tab, setTab] = React.useState("activity");
  const switchedToSummary = React.useRef(false);

  React.useEffect(() => {
    api.getRun(runId).then(setDetail).catch(() => setDetail(null));
  }, [runId]);

  const stream = useRunStream(runId, detail?.run.status ?? "pending");
  const finished = stream.finished;

  // Once the run finishes, refetch the authoritative detail (outputs, summary,
  // score, final duration) and refresh the artifact explorer.
  React.useEffect(() => {
    if (finished) {
      api.getRun(runId).then((d) => {
        setDetail(d);
        setRefreshKey((k) => k + 1);
      });
      if (!switchedToSummary.current) {
        switchedToSummary.current = true;
        setTab("summary");
      }
    }
  }, [finished, runId]);

  const steps = React.useMemo(() => deriveSteps(stream.events), [stream.events]);
  const progress = overallProgress(steps, finished);
  const iteration = stream.events.reduce((m, e) => Math.max(m, e.iteration), 0);

  const status: RunStatus = finished
    ? detail?.run.status ?? "completed"
    : stream.events.length > 0
      ? "running"
      : detail?.run.status ?? "pending";

  const score = React.useMemo(() => {
    const ev = [...stream.events]
      .reverse()
      .find((e) => e.type === "run_completed" || (e.type === "agent_completed" && e.agent === "code_reviewer"));
    return (ev?.data?.score as number) ?? detail?.run.review_score ?? null;
  }, [stream.events, detail]);

  if (!detail) {
    return (
      <div className="container space-y-4 py-8">
        <Skeleton className="h-32" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="container space-y-6 py-8">
      <RunHeader
        detail={detail}
        status={status}
        progress={progress}
        score={score}
        durationMs={finished ? detail.run.duration_ms : null}
        iteration={iteration}
        finished={finished}
      />

      <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
        {/* Left: orchestration view */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Sparkles className="h-4 w-4 text-primary" /> Workflow
              </CardTitle>
            </CardHeader>
            <CardContent>
              <WorkflowGraph steps={steps} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Agent timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <AgentTimeline steps={steps} />
            </CardContent>
          </Card>
        </div>

        {/* Right: tabbed detail */}
        <div>
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList>
              <TabsTrigger value="activity">
                <span className="flex items-center gap-1.5">
                  <Activity className="h-3.5 w-3.5" /> Activity
                </span>
              </TabsTrigger>
              <TabsTrigger value="artifacts">
                <span className="flex items-center gap-1.5">
                  <FolderTree className="h-3.5 w-3.5" /> Workspace
                </span>
              </TabsTrigger>
              <TabsTrigger value="summary">
                <span className="flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5" /> Summary
                </span>
              </TabsTrigger>
            </TabsList>

            <div className="mt-4">
              <TabsContent value="activity">
                <Card>
                  <CardContent className="pt-5">
                    <ActivityFeed events={stream.events} live={!finished} />
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="artifacts">
                <ArtifactExplorer runId={runId} refreshKey={refreshKey} />
              </TabsContent>

              <TabsContent value="summary">
                <DeliverySummary detail={detail} finished={finished} />
              </TabsContent>
            </div>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
