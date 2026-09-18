import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  glass?: boolean;
  glow?: boolean;
}

export function GlassCard({
  className,
  glass = true,
  glow = true,
  children,
  ...props
}: GlassCardProps) {
  return (
    <div
      className={cn(
        "pastel-border relative rounded-2xl",
        glass && "glass-card",
        glow && "pastel-shadow",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}