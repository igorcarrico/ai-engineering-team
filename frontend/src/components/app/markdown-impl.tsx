"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { cn } from "@/lib/utils";

/** Markdown renderer with hand-tuned styles (no typography plugin dependency).
 *  Loaded client-only via the wrapper in `markdown.tsx` because react-markdown
 *  is ESM-only and must not be imported during server rendering. */
export function Markdown({ content, className }: { content: string; className?: string }) {
  return (
    <div className={cn("text-sm leading-relaxed text-foreground/90", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: (p) => <h1 className="mb-3 mt-1 text-xl font-bold tracking-tight" {...p} />,
          h2: (p) => (
            <h2 className="mb-2 mt-6 border-b border-border/60 pb-1 text-lg font-semibold" {...p} />
          ),
          h3: (p) => <h3 className="mb-1.5 mt-4 text-base font-semibold" {...p} />,
          p: (p) => <p className="mb-3 text-muted-foreground" {...p} />,
          ul: (p) => <ul className="mb-3 ml-5 list-disc space-y-1 text-muted-foreground" {...p} />,
          ol: (p) => <ol className="mb-3 ml-5 list-decimal space-y-1 text-muted-foreground" {...p} />,
          li: (p) => <li className="marker:text-primary/60" {...p} />,
          strong: (p) => <strong className="font-semibold text-foreground" {...p} />,
          a: (p) => <a className="text-primary underline-offset-2 hover:underline" {...p} />,
          blockquote: (p) => (
            <blockquote className="my-3 border-l-2 border-primary/40 pl-3 italic text-muted-foreground" {...p} />
          ),
          table: (p) => (
            <div className="my-3 overflow-x-auto rounded-lg border border-border/60">
              <table className="w-full text-left text-xs" {...p} />
            </div>
          ),
          th: (p) => <th className="bg-secondary/50 px-3 py-2 font-semibold" {...p} />,
          td: (p) => <td className="border-t border-border/40 px-3 py-2 text-muted-foreground" {...p} />,
          code: ({ className: c, children, ...rest }) => {
            const isBlock = /language-/.test(c || "");
            if (isBlock) {
              return (
                <code className={cn("font-mono text-[13px]", c)} {...rest}>
                  {children}
                </code>
              );
            }
            return (
              <code className="rounded bg-secondary px-1.5 py-0.5 font-mono text-[12px] text-foreground" {...rest}>
                {children}
              </code>
            );
          },
          pre: (p) => (
            <pre
              className="scrollbar-thin my-3 overflow-x-auto rounded-lg border border-border/60 bg-[hsl(var(--muted))]/40 p-4"
              {...p}
            />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
