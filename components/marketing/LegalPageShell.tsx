import type { ReactNode } from "react";
import { AlertTriangle, ShieldCheck } from "lucide-react";
import AuroraBackdrop from "@/components/AuroraBackdrop";
import PublicFooter from "@/components/marketing/PublicFooter";
import PublicHeader from "@/components/marketing/PublicHeader";
import { CONTACT_EMAIL, LEGAL_LAST_UPDATED } from "@/lib/site";

interface LegalPageShellProps {
  title: string;
  summary: string;
  reviewNotes: string[];
  children: ReactNode;
}

export function LegalPageShell({
  title,
  summary,
  reviewNotes,
  children,
}: LegalPageShellProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <PublicHeader />

      <div className="relative overflow-hidden border-b border-border">
        <AuroraBackdrop className="opacity-60" />
        <div className="relative z-10 mx-auto max-w-3xl px-6 py-14 sm:py-20">
          <p className="triage-label inline-flex items-center gap-2 text-muted-foreground">
            <ShieldCheck size={14} aria-hidden />
            Legal
          </p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
            {title}
          </h1>
          <p className="mt-4 max-w-2xl text-pretty text-base leading-relaxed text-muted-foreground">
            {summary}
          </p>
          <p className="mt-6 text-xs text-muted-foreground">
            Last updated: {LEGAL_LAST_UPDATED}
          </p>
        </div>
      </div>

      <main className="mx-auto max-w-3xl px-6 py-12 sm:py-16">
        <div
          role="note"
          aria-label="Review notes"
          className="mb-12 rounded-2xl border border-amber-500/30 bg-amber-50/70 p-5 text-sm text-amber-900 dark:border-amber-400/25 dark:bg-amber-400/10 dark:text-amber-100"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle size={18} className="mt-0.5 shrink-0" aria-hidden />
            <div>
              <p className="font-semibold">
                Academic project — items to review before public launch
              </p>
              <p className="mt-1 text-amber-800/90 dark:text-amber-100/80">
                This document describes the current implementation as accurately
                as possible. The items below still need confirmation from the
                project author or a legal advisor:
              </p>
              <ul className="mt-3 list-disc space-y-1.5 pl-5">
                {reviewNotes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <article className="space-y-10">{children}</article>

        <div className="mt-12 rounded-2xl border border-border bg-card p-5 text-sm text-muted-foreground">
          Questions about this page? Email{" "}
          <a
            href={`mailto:${CONTACT_EMAIL}`}
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            {CONTACT_EMAIL}
          </a>
          .
        </div>
      </main>

      <PublicFooter />
    </div>
  );
}

export function LegalSection({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section id={id} aria-labelledby={`${id}-heading`} className="scroll-mt-24">
      <h2
        id={`${id}-heading`}
        className="text-lg font-semibold tracking-tight sm:text-xl"
      >
        {title}
      </h2>
      <div className="mt-3 space-y-3 text-sm leading-7 text-muted-foreground">
        {children}
      </div>
    </section>
  );
}

export function LegalList({ children }: { children: ReactNode }) {
  return <ul className="list-disc space-y-1.5 pl-5">{children}</ul>;
}
