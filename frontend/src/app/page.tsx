import { GitBranch, Layers, Radio, ShieldCheck } from "lucide-react";

import { CreatePanel } from "@/components/app/create-panel";
import { ProjectList } from "@/components/app/project-list";
import { AGENT_SEQUENCE, AGENT_META } from "@/lib/agents";

const HIGHLIGHTS = [
  { icon: GitBranch, title: "LangGraph orchestration", desc: "Stateful graph with parallel fan-out, a join, and a conditional refine loop." },
  { icon: Radio, title: "Live activity stream", desc: "Every agent action streams to the UI over Server-Sent Events." },
  { icon: Layers, title: "Real artifacts", desc: "Specs, architecture, code files, QA & security reports — exportable." },
  { icon: ShieldCheck, title: "Runs key-free", desc: "A deterministic mock provider runs the whole platform with no API keys." },
];

export default function HomePage() {
  return (
    <div className="relative">
      <div className="pointer-events-none absolute inset-0 grid-bg opacity-60" />

      <section className="container relative pt-16 sm:pt-24">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-border/70 bg-secondary/40 px-3 py-1 text-xs text-muted-foreground">
            <span className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-primary" />
            8 specialized agents · 1 orchestrated workflow
          </div>
          <h1 className="text-balance text-4xl font-bold tracking-tight sm:text-6xl">
            Your autonomous <span className="text-gradient">AI engineering team</span>
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-pretty text-base text-muted-foreground sm:text-lg">
            Describe a software idea. A virtual team of AI agents — Product Manager, Architect,
            Engineers, QA, Security and a Reviewer — collaborates through a LangGraph workflow to
            produce a structured engineering plan and real artifacts.
          </p>
        </div>

        <div className="mx-auto mt-10 max-w-2xl">
          <CreatePanel />
        </div>

        {/* Agent lineup */}
        <div className="mx-auto mt-8 flex max-w-3xl flex-wrap items-center justify-center gap-2">
          {AGENT_SEQUENCE.map((key) => {
            const meta = AGENT_META[key];
            const Icon = meta.icon;
            return (
              <div
                key={key}
                className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs ${meta.bg} ${meta.ring} ring-1`}
              >
                <Icon className={`h-3.5 w-3.5 ${meta.text}`} />
                <span className="text-foreground/90">{meta.label}</span>
              </div>
            );
          })}
        </div>
      </section>

      {/* Highlights */}
      <section className="container relative mt-20">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {HIGHLIGHTS.map((h) => {
            const Icon = h.icon;
            return (
              <div key={h.title} className="rounded-xl border border-border/60 bg-card/40 p-5">
                <Icon className="h-5 w-5 text-primary" />
                <h3 className="mt-3 text-sm font-semibold">{h.title}</h3>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{h.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Recent projects */}
      <section className="container relative mb-20 mt-16">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Recent runs</h2>
        </div>
        <ProjectList />
      </section>
    </div>
  );
}
