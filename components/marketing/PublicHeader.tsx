import Link from "next/link";
import { Inbox } from "lucide-react";
import ThemeToggle from "@/components/ThemeToggle";
import { Button } from "@/components/ui/button";
import { BRAND_NAME } from "@/lib/brand";
import { PUBLIC_LINKS } from "@/lib/site";

export default function PublicHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-background/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-2 px-4 py-3 sm:px-6">
        <Link
          href={PUBLIC_LINKS.home}
          className="flex items-center gap-2.5 rounded-lg focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
          aria-label={`${BRAND_NAME} home`}
        >
          <span className="flex size-8 items-center justify-center rounded-lg bg-linear-to-br from-signal to-violet-400 text-primary-foreground shadow-sm">
            <Inbox size={15} strokeWidth={2} aria-hidden />
          </span>
          <span className="text-[15px] font-semibold tracking-tight">
            {BRAND_NAME}
          </span>
        </Link>

        <nav
          aria-label="Main navigation"
          className="hidden items-center gap-6 text-sm text-muted-foreground md:flex"
        >
          <Link
            href={PUBLIC_LINKS.features}
            className="transition-colors hover:text-foreground"
          >
            Features
          </Link>
          <Link
            href={PUBLIC_LINKS.howItWorks}
            className="transition-colors hover:text-foreground"
          >
            How it works
          </Link>
          <Link
            href={PUBLIC_LINKS.privacy}
            className="transition-colors hover:text-foreground"
          >
            Privacy
          </Link>
          <Link
            href={PUBLIC_LINKS.terms}
            className="transition-colors hover:text-foreground"
          >
            Terms
          </Link>
        </nav>

        <div className="flex items-center gap-1.5">
          <ThemeToggle />
          <Button variant="ghost" size="sm" render={<Link href={PUBLIC_LINKS.login} />}>
            Sign in
          </Button>
          <Button size="sm" render={<Link href={PUBLIC_LINKS.signup} />}>
            Get Started
          </Button>
        </div>
      </div>
    </header>
  );
}
