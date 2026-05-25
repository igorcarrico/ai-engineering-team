import {
  Boxes,
  Brain,
  Code2,
  Layout,
  type LucideIcon,
  ShieldCheck,
  Sparkles,
  TestTube2,
  Workflow,
} from "lucide-react";

import type { AgentKey } from "./types";

export interface AgentMeta {
  key: AgentKey;
  label: string;
  short: string;
  blurb: string;
  icon: LucideIcon;
  /** Tailwind classes for accenting this agent. */
  text: string;
  bg: string;
  ring: string;
  dot: string;
}

export const AGENT_META: Record<AgentKey, AgentMeta> = {
  product_manager: {
    key: "product_manager",
    label: "Product Manager",
    short: "PM",
    blurb: "Defines vision, user stories, MVP scope, risks.",
    icon: Brain,
    text: "text-sky-400",
    bg: "bg-sky-500/10",
    ring: "ring-sky-500/30",
    dot: "bg-sky-400",
  },
  architect: {
    key: "architect",
    label: "Software Architect",
    short: "ARCH",
    blurb: "Designs architecture, data model and API surface.",
    icon: Boxes,
    text: "text-violet-400",
    bg: "bg-violet-500/10",
    ring: "ring-violet-500/30",
    dot: "bg-violet-400",
  },
  backend_engineer: {
    key: "backend_engineer",
    label: "Backend Engineer",
    short: "BE",
    blurb: "Service modules, endpoints and starter code.",
    icon: Code2,
    text: "text-emerald-400",
    bg: "bg-emerald-500/10",
    ring: "ring-emerald-500/30",
    dot: "bg-emerald-400",
  },
  frontend_engineer: {
    key: "frontend_engineer",
    label: "Frontend Engineer",
    short: "FE",
    blurb: "Pages, components and UI implementation.",
    icon: Layout,
    text: "text-cyan-400",
    bg: "bg-cyan-500/10",
    ring: "ring-cyan-500/30",
    dot: "bg-cyan-400",
  },
  qa_engineer: {
    key: "qa_engineer",
    label: "QA Engineer",
    short: "QA",
    blurb: "Test strategy, scenarios and missing requirements.",
    icon: TestTube2,
    text: "text-amber-400",
    bg: "bg-amber-500/10",
    ring: "ring-amber-500/30",
    dot: "bg-amber-400",
  },
  security_reviewer: {
    key: "security_reviewer",
    label: "Security Reviewer",
    short: "SEC",
    blurb: "Threat surface, auth and prompt-injection risks.",
    icon: ShieldCheck,
    text: "text-rose-400",
    bg: "bg-rose-500/10",
    ring: "ring-rose-500/30",
    dot: "bg-rose-400",
  },
  code_reviewer: {
    key: "code_reviewer",
    label: "Code Reviewer",
    short: "REV",
    blurb: "Cross-checks quality and decides approve/revise.",
    icon: Sparkles,
    text: "text-fuchsia-400",
    bg: "bg-fuchsia-500/10",
    ring: "ring-fuchsia-500/30",
    dot: "bg-fuchsia-400",
  },
  supervisor: {
    key: "supervisor",
    label: "Supervisor",
    short: "SUP",
    blurb: "Coordinates the workflow and finalizes delivery.",
    icon: Workflow,
    text: "text-indigo-400",
    bg: "bg-indigo-500/10",
    ring: "ring-indigo-500/30",
    dot: "bg-indigo-400",
  },
};

export const AGENT_SEQUENCE: AgentKey[] = [
  "product_manager",
  "architect",
  "backend_engineer",
  "frontend_engineer",
  "qa_engineer",
  "security_reviewer",
  "code_reviewer",
];

export function agentMeta(key: AgentKey | null | undefined): AgentMeta {
  return (key && AGENT_META[key]) || AGENT_META.supervisor;
}
