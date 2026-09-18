import { cn } from "@/lib/utils";

/**
 * Decorative, fully CSS-driven soft gradient backdrop (blue → pink → yellow).
 * Pure presentational layer — pointer-events are disabled and it should be
 * mounted with `absolute inset-0` inside a `relative overflow-hidden` parent.
 */
export default function AuroraBackdrop({
  className,
}: {
  className?: string;
}) {
  return (
    <div
      aria-hidden
      className={cn(
        "pointer-events-none absolute inset-0 overflow-hidden",
        className
      )}
    >
      <div className="absolute -top-32 -left-32 size-[36rem] rounded-full bg-sky-200/50 blur-3xl motion-reduce:animate-none animate-drift-a dark:bg-sky-500/10" />
      <div className="absolute top-1/4 -right-40 size-[32rem] rounded-full bg-pink-200/50 blur-3xl motion-reduce:animate-none animate-drift-b dark:bg-pink-500/10" />
      <div className="absolute bottom-[-6rem] left-1/3 size-[30rem] rounded-full bg-amber-100/70 blur-3xl motion-reduce:animate-none animate-drift-c dark:bg-amber-400/10" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,_oklch(0.98_0.02_250/0.6),transparent_70%)]" />
    </div>
  );
}