"use client";

import { ArrowRight, Loader2, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";

const EXAMPLES = [
  "A SaaS platform for AI-powered financial analytics",
  "A marketplace connecting freelance designers with startups",
  "A habit-tracking mobile app with social accountability",
  "An internal tool for managing customer support SLAs",
];

export function CreatePanel() {
  const router = useRouter();
  const [idea, setIdea] = React.useState("");
  const [constraints, setConstraints] = React.useState("");
  const [showAdvanced, setShowAdvanced] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function submit() {
    if (idea.trim().length < 8) {
      setError("Describe your idea in a little more detail (8+ characters).");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const detail = await api.createProject({
        idea: idea.trim(),
        constraints: constraints.trim() || undefined,
      });
      router.push(`/runs/${detail.run.id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong. Is the API running?");
      setLoading(false);
    }
  }

  return (
    <Card className="glass overflow-hidden">
      <CardContent className="p-6">
        <div className="mb-3 flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <Sparkles className="h-4 w-4 text-primary" />
          Describe the idea you're evaluating
        </div>
        <Textarea
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          placeholder="e.g. An internal analytics dashboard for fleet fuel-consumption optimization…"
          className="min-h-[120px] text-base"
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter") submit();
          }}
        />

        <div className="mt-3 flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => setIdea(ex)}
              className="rounded-full border border-border/70 bg-secondary/40 px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
            >
              {ex}
            </button>
          ))}
        </div>

        {showAdvanced && (
          <div className="mt-4 animate-fade-in-up">
            <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
              Constraints (optional)
            </label>
            <Input
              value={constraints}
              onChange={(e) => setConstraints(e.target.value)}
              placeholder="e.g. must run on AWS, GDPR compliant, ship in 6 weeks"
            />
          </div>
        )}

        {error && (
          <p className="mt-3 text-sm text-[hsl(var(--danger))]">{error}</p>
        )}

        <div className="mt-5 flex items-center justify-between">
          <button
            onClick={() => setShowAdvanced((v) => !v)}
            className="text-xs text-muted-foreground underline-offset-4 hover:underline"
          >
            {showAdvanced ? "Hide" : "Add"} constraints
          </button>
          <Button size="lg" onClick={submit} disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Assembling team…
              </>
            ) : (
              <>
                Get the verdict
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
