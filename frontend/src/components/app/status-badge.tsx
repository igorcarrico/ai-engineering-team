import { CheckCircle2, CircleDashed, Loader2, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { RunStatus, StepStatus } from "@/lib/types";

export function StatusBadge({ status }: { status: RunStatus | StepStatus }) {
  switch (status) {
    case "completed":
      return (
        <Badge variant="success">
          <CheckCircle2 className="h-3 w-3" /> Completed
        </Badge>
      );
    case "running":
      return (
        <Badge variant="default">
          <Loader2 className="h-3 w-3 animate-spin" /> Running
        </Badge>
      );
    case "failed":
      return (
        <Badge variant="danger">
          <XCircle className="h-3 w-3" /> Failed
        </Badge>
      );
    case "pending":
      return (
        <Badge variant="outline">
          <CircleDashed className="h-3 w-3" /> Pending
        </Badge>
      );
    default:
      return <Badge variant="secondary">{status}</Badge>;
  }
}
