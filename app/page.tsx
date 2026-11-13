import Link from "next/link";
import {
  ArrowRight,
  BrainCircuit,
  FileText,
  Focus,
  Inbox,
  Layers,
  ListChecks,
  Plug,
  Sparkles,
} from "lucide-react";
import PublicFooter from "@/components/marketing/PublicFooter";
import PublicHeader from "@/components/marketing/PublicHeader";
import { Button } from "@/components/ui/button";
import { BRAND_NAME } from "@/lib/brand";
import { PUBLIC_LINKS } from "@/lib/site";

const features = [
  {
    icon: BrainCircuit,
    title: "Intelligent Message Prioritization",
    body: "AI scores every message — urgent, important, normal, or low — so the messages that actually need you rise to the top.",
  },
  {
    icon: FileText,
    title: "AI-Powered Summaries",
    body: "Long threads become short summaries with the key point and a recommended action, so you can catch up in seconds.",
  },
  {
    icon: ListChecks,
    title: "Automatic Task Extraction",
    body: "Deadlines, to-dos, and follow-ups are pulled from conversations into a task list you can act on.",
  },
  {
    icon: Layers,
    title: "Communication Overload Management",
    body: "Gmail and WhatsApp flow into one calm inbox with an attention view, analytics, and an assistant that answers questions.",
  },
];

const steps = [
  {
    icon: Plug,
    title: "Connect your channels",
    body: "Connect Gmail with read-only Google OAuth, or ingest WhatsApp messages through the webhook.",
  },
  {
    icon: Sparkles,
    title: "AI analyzes & prioritizes",
    body: "Every message is routed, summarized, and triaged in a single AI pass.",
  },
  {
    icon: Focus,
    title: "Focus on what matters",
    body: "Check the Attention tab, complete extracted tasks, and act on the messages that matter.",
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <PublicHeader />

      {/* ===== Hero backdrop ===== */}
      <div className="relative overflow-hidden">
        <div aria-hidden className="pointer-events-none absolute inset-0">
          <div className="absolute -top-32 -left-24 size-[34rem] rounded-full bg-sky-300/30 blur-3xl motion-reduce:animate-none animate-drift-a dark:bg-sky-500/15" />
          <div className="absolute -top-16 right-[-10rem] size-[30rem] rounded-full bg-pink-300/30 blur-3xl motion-reduce:animate-none animate-drift-b dark:bg-pink-500/15" />
          <div className="absolute top-40 left-1/2 size-[26rem] -translate-x-1/2 rounded-full bg-amber-200/40 blur-3xl motion-reduce:animate-none animate-drift-c dark:bg-amber-400/15" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,_oklch(0.98_0.02_250/0.5),transparent)]" />
        </div>

        {/* ===== Hero ===== */}
        <section className="relative z-10 mx-auto max-w-3xl px-4 pt-14 pb-24 text-center sm:pt-20">
          <div className="relative">
            <div
              aria-hidden
              className="absolute -inset-2 -z-10 rounded-[2rem] bg-linear-to-br from-sky-300/40 via-pink-200/40 to-amber-200/40 blur-2xl"
            />
            <div className="rounded-[2rem] bg-linear-to-br from-sky-200 via-pink-200 to-amber-100 p-px bg-[length:220%_220%] animate-pan dark:from-sky-400/30 dark:via-pink-400/25 dark:to-amber-300/25">
              <div className="rounded-[calc(2rem-1px)] bg-white/80 px-6 py-14 backdrop-blur-xl sm:px-12 dark:bg-surface/70">
                <div className="mb-5 flex items-center justify-center gap-2.5">
                  <span className="flex size-9 items-center justify-center rounded-xl bg-linear-to-br from-signal to-violet-400 text-primary-foreground shadow-md shadow-signal/25">
                    <Inbox size={18} strokeWidth={2} />
                  </span>
                  <span className="text-sm font-semibold tracking-tight">
                    {BRAND_NAME}
                  </span>
                </div>

                <h1 className="text-balance text-4xl leading-[1.1] font-semibold tracking-tight sm:text-5xl">
                  Read everything.{" "}
                  <span className="bg-linear-to-r from-signal via-fuchsia-500 to-ember bg-clip-text text-transparent">
                    Surface what matters.
                  </span>
                </h1>

                <p className="mx-auto mt-5 max-w-xl text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg">
                  An intelligent AI inbox that prioritizes messages,
                  summarizes threads, and extracts tasks so you never miss what
                  counts.
                </p>

                <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
                  <Button
                    className="h-11 w-full rounded-full bg-foreground px-7 text-[15px] text-background hover:bg-foreground/90 sm:w-auto"
                    render={<Link href={PUBLIC_LINKS.signup} />}
                  >
                    Get Started
                    <ArrowRight className="ml-1" />
                  </Button>
                  <Button
                    variant="outline"
                    className="h-11 w-full rounded-full px-7 text-[15px] sm:w-auto"
                    render={<Link href={PUBLIC_LINKS.howItWorks} />}
                  >
                    See how it works
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* ===== Features ===== */}
      <section id="features" className="mx-auto max-w-6xl scroll-mt-24 px-6 pb-24">
        <div className="mx-auto max-w-2xl text-center">
          <p className="triage-label text-muted-foreground">Features</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
            One inbox, no overload
          </h2>
          <p className="mt-3 text-base text-muted-foreground">
            Everything lands in one place, and AI does the sorting for you.
          </p>
        </div>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="rounded-2xl border border-border bg-card p-6 shadow-sm transition-shadow duration-300 hover:shadow-md"
            >
              <span className="inline-flex size-11 items-center justify-center rounded-xl bg-signal-dim text-signal">
                <feature.icon size={20} strokeWidth={1.75} />
              </span>
              <h3 className="mt-4 text-[15px] font-semibold tracking-tight">
                {feature.title}
              </h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                {feature.body}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ===== How it works ===== */}
      <section
        id="how-it-works"
        className="scroll-mt-24 border-y border-border bg-muted/60 py-20"
      >
        <div className="mx-auto max-w-6xl px-6">
          <div className="mx-auto max-w-2xl text-center">
            <p className="triage-label text-muted-foreground">How it works</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
              Calm in three steps
            </h2>
          </div>

          <div className="relative mt-14 grid gap-12 sm:grid-cols-3 sm:gap-8">
            <div
              aria-hidden
              className="absolute top-6 right-[16.66%] left-[16.66%] hidden h-px bg-linear-to-r from-transparent via-hairline to-transparent lg:block"
            />
            {steps.map((step, index) => (
              <div
                key={step.title}
                className="relative flex flex-col items-center text-center"
              >
                <span className="relative z-10 flex size-12 items-center justify-center rounded-2xl border border-border bg-card text-signal shadow-sm">
                  <step.icon size={20} strokeWidth={1.75} />
                </span>
                <span className="triage-label mt-5 text-muted-foreground">
                  Step {index + 1}
                </span>
                <h3 className="mt-1.5 text-lg font-semibold tracking-tight">
                  {step.title}
                </h3>
                <p className="mt-2 max-w-xs text-sm leading-relaxed text-muted-foreground">
                  {step.body}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-14 text-center">
            <Button
              className="h-11 rounded-full bg-foreground px-7 text-[15px] text-background hover:bg-foreground/90"
              render={<Link href={PUBLIC_LINKS.signup} />}
            >
              Get Started
              <ArrowRight className="ml-1" />
            </Button>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}