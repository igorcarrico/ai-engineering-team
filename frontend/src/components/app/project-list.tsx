"use client";

import { ArrowUpRight, FileStack, FolderGit2 } from "lucide-react";
import Link from "next/link";
import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/misc";
import { StatusBadge } from "@/components/app/status-badge";
import { api } from "@/lib/api";
import type { ProjectSummary } from "@/lib/types";
import { relativeTime } from "@/lib/utils";

export function ProjectList() {
  const [projects, setProjects] = React.useState<ProjectSummary[] | null>(null);

  React.useEffect(() => {
    api.listProjects().then(setProjects).catch(() => setProjects([]));
  }, []);

  if (projects === null) {
    return (
      <div className="grid gap-3 sm:grid-cols-2">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-12 text-center">
        <FolderGit2 className="mb-3 h-8 w-8 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          No projects yet. Launch your first engineering run above.
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {projects.map((p) => (
        <Link key={p.id} href={p.latest_run_id ? `/runs/${p.latest_run_id}` : "#"}>
          <Card className="group h-full p-4 transition-all hover:border-primary/40 hover:shadow-lg hover:shadow-primary/5">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="truncate font-semibold">{p.name}</h3>
                  <ArrowUpRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                </div>
                <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{p.idea}</p>
              </div>
              {p.latest_status && <StatusBadge status={p.latest_status} />}
            </div>
            <div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
              <span>{relativeTime(p.created_at)}</span>
              {p.artifact_count > 0 && (
                <span className="flex items-center gap-1">
                  <FileStack className="h-3 w-3" />
                  {p.artifact_count} artifacts
                </span>
              )}
              {p.review_score != null && (
                <Badge variant="secondary" className="ml-auto">
                  {p.review_score}/100
                </Badge>
              )}
            </div>
          </Card>
        </Link>
      ))}
    </div>
  );
}
