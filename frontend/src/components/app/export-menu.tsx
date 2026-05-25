"use client";

import { Braces, Download, FileText, Package } from "lucide-react";

import { api } from "@/lib/api";

const ITEMS = [
  { fmt: "md" as const, label: "Markdown", icon: FileText },
  { fmt: "json" as const, label: "JSON", icon: Braces },
  { fmt: "zip" as const, label: "Workspace .zip", icon: Package },
];

export function ExportMenu({ runId, disabled }: { runId: string; disabled?: boolean }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="hidden items-center gap-1 text-xs text-muted-foreground sm:flex">
        <Download className="h-3.5 w-3.5" /> Export
      </span>
      {ITEMS.map(({ fmt, label, icon: Icon }) => (
        <a
          key={fmt}
          href={disabled ? undefined : api.exportUrl(runId, fmt)}
          aria-disabled={disabled}
          className={`inline-flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1.5 text-xs font-medium transition-colors ${
            disabled
              ? "pointer-events-none opacity-40"
              : "hover:border-primary/40 hover:bg-secondary/60"
          }`}
        >
          <Icon className="h-3.5 w-3.5" />
          {label}
        </a>
      ))}
    </div>
  );
}
