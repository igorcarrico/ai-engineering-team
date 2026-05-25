"use client";

import dynamic from "next/dynamic";

/**
 * Client-only Markdown.
 *
 * react-markdown (and its remark/micromark ESM dependency chain) must not be
 * imported during server rendering, so we load the implementation lazily with
 * `ssr: false`. Markdown is only ever shown after a client-side data fetch, so
 * there's nothing to render on the server anyway.
 */
export const Markdown = dynamic<{ content: string; className?: string }>(
  () => import("./markdown-impl").then((m) => m.Markdown),
  {
    ssr: false,
    loading: () => <div className="text-sm text-muted-foreground">Rendering…</div>,
  },
);
