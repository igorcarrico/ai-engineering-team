import * as React from "react";

import { cn } from "@/lib/utils";

type Variant = "default" | "secondary" | "outline" | "success" | "warning" | "danger";

const variants: Record<Variant, string> = {
  default: "bg-primary/15 text-primary border-primary/20",
  secondary: "bg-secondary text-secondary-foreground border-transparent",
  outline: "border-border text-muted-foreground",
  success: "bg-[hsl(var(--success))]/15 text-[hsl(var(--success))] border-[hsl(var(--success))]/20",
  warning: "bg-[hsl(var(--warning))]/15 text-[hsl(var(--warning))] border-[hsl(var(--warning))]/20",
  danger: "bg-[hsl(var(--danger))]/15 text-[hsl(var(--danger))] border-[hsl(var(--danger))]/20",
};

export function Badge({
  className,
  variant = "default",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: Variant }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
