import Link from "next/link";
import {
  ArrowRight,
  BrainCircuit,
  Focus,
  Inbox,
  ListChecks,
  MessageSquareText,
  Plug,
  Sparkles,
} from "lucide-react";
import ThemeToggle from "@/components/ThemeToggle";
import { Button } from "@/components/ui/button";

const features = [
  {
    icon: BrainCircuit,
    title: "Smart Priority Detection",
    body: "AI reads every message and flags what actually needs you now. Urgent goes first, noise stays quiet.",
  },
  {
    icon: ListChecks,
    title: "Automatic Task Extraction",
    body: "Deadlines and to-dos are pulled straight from conversations into a task list you can tick off.",
  },
  {
    icon: MessageSquareText,
    title: "AI Reply Suggestions",
    body: "Context-aware replies are drafted for you, so responding takes seconds instead of minutes.",
  },
  {
    icon: Inbox,
    title: "Unified Inbox",
    body: "WhatsApp and Gmail land in one calm inbox — automatically threaded, prioritized, and summarized.",
  },
];

const steps = [
  {
    icon: Plug,
    title: "Connect your channels",
    body: "Link WhatsApp and Gmail in two clicks with secure, encrypted OAuth.",
  },
  {
    icon: Sparkles,
    title: "AI analyzes & prioritizes",
    body: "Every message is routed, summarized, and triaged in a single AI pass.",
  },
  {
    icon: Focus,
    title: "Focus on what matters",
    body: "Check the Attention tab, complete extracted tasks, and reply in seconds.",
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* ===== Hero backdrop ===== */}
      <div className="relative overflow-hidden">
        <div aria-hidden className="pointer-events-none absolute inset-0">
          <div className="absolute -top-32 -left-24 size-[34rem] rounded-full bg-sky-300/30 blur-3xl motion-reduce:animate-none animate-drift-a dark:bg-sky-500/15" />
          <div className="absolute -top-16 right-[-10rem] size-[30rem] rounded-full bg-pink-300/30 blur-3xl motion-reduce:animate-none animate-drift-b dark:bg-pink-500/15" />
          <div className="absolute top-40 left-1/2 size-[26rem] -translate-x-1/2 rounded-full bg-amber-200/40 blur-3xl motion-reduce:animate-none animate-drift-c dark:bg-amber-400/15" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,_oklch(0.98_0.02_250/0.5),transparent)]" />
        </div>

        {/* ===== Nav ===== */}
        <header className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="flex size-8 items-center justify-center rounded-lg bg-linear-to-br from-signal to-violet-400 text-primary-foreground shadow-sm">
              <Inbox size={15} strokeWidth={2} />
            </span>
            <span className="text-[15px] font-semibold tracking-tight">
              Signal Desk
            </span>
          </Link>
          <div className="flex items-center gap-2">
            <ThemeToggle className="hidden md:inline-flex" />
            <Button
              variant="ghost"
              size="sm"
              render={<Link href="/login" />}
            >
              Sign in
            </Button>
            <Button
              size="sm"
              render={<Link href="/signup" />}
            >
              Get Started
            </Button>
          </div>
        </header>

        {/* ===== Hero ===== */}
        <section className="relative z-10 mx-auto max-w-3xl px-4 pt-6 pb-24 text-center sm:pt-10">
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
                    Signal Desk
                  </span>
                </div>

                <h1 className="text-balance text-4xl leading-[1.1] font-semibold tracking-tight sm:text-5xl">
                  Read everything.{" "}
                  <span className="bg-linear-to-r from-signal via-fuchsia-500 to-ember bg-clip-text text-transparent">
                    Surface what matters.
                  </span>
                </h1>

                <p className="mx-auto mt-5 max-w-xl text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg">
                  An intelligent AI inbox that prioritizes messages, extracts
                  tasks, and suggests smart replies so you never miss what
                  counts.
                </p>

                <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
                  <Button
                    className="h-11 w-full rounded-full bg-foreground px-7 text-[15px] text-background hover:bg-foreground/90 sm:w-auto"
                    render={<Link href="/signup" />}
                  >
                    Get Started
                    <ArrowRight className="ml-1" />
                  </Button>
                  <Button
                    variant="outline"
                    className="h-11 w-full rounded-full px-7 text-[15px] sm:w-auto"
                    render={<Link href="/dashboard" />}
                  >
                    View Demo
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* ===== Features ===== */}
      <section className="mx-auto max-w-6xl px-6 pb-24">
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
      <section className="border-y border-border bg-muted/60 py-20">
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
              render={<Link href="/signup" />}
            >
              Get Started
              <ArrowRight className="ml-1" />
            </Button>
          </div>
        </div>
      </section>

      {/* ===== Footer ===== */}
      <footer className="bg-background">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-10 sm:flex-row">
          <div className="flex items-center gap-2.5">
            <span className="flex size-7 items-center justify-center rounded-lg bg-linear-to-br from-signal to-violet-400 text-primary-foreground">
              <Inbox size={14} strokeWidth={2} />
            </span>
            <span className="text-sm font-semibold tracking-tight">
              Signal Desk
            </span>
          </div>
          <p className="text-center text-xs text-muted-foreground">
            AI-powered communication overload management.
          </p>
          <p className="text-xs text-muted-foreground">
            Built as Final Year Project – BBSUL
          </p>
        </div>
      </footer>
    </div>
  );
}