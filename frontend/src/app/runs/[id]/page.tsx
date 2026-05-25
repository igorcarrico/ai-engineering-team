import { RunDashboard } from "@/components/app/run-dashboard";

export default function RunPage({ params }: { params: { id: string } }) {
  return <RunDashboard runId={params.id} />;
}
