import Link from "next/link";
import { Inbox, Mail } from "lucide-react";
import { BRAND_NAME } from "@/lib/brand";
import { CONTACT_EMAIL, LEGAL_LAST_UPDATED, PUBLIC_LINKS } from "@/lib/site";

const productLinks = [
  { href: PUBLIC_LINKS.features, label: "Features" },
  { href: PUBLIC_LINKS.howItWorks, label: "How it works" },
  { href: PUBLIC_LINKS.signup, label: "Get started" },
  { href: PUBLIC_LINKS.login, label: "Sign in" },
];

const legalLinks = [
  { href: PUBLIC_LINKS.privacy, label: "Privacy Policy" },
  { href: PUBLIC_LINKS.terms, label: "Terms of Service" },
];

export default function PublicFooter() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto grid max-w-6xl gap-10 px-6 py-12 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <Link href={PUBLIC_LINKS.home} className="flex items-center gap-2.5">
            <span className="flex size-8 items-center justify-center rounded-lg bg-linear-to-br from-signal to-violet-400 text-primary-foreground shadow-sm">
              <Inbox size={15} strokeWidth={2} aria-hidden />
            </span>
            <span className="text-[15px] font-semibold tracking-tight">
              {BRAND_NAME}
            </span>
          </Link>
          <p className="mt-3 max-w-xs text-sm leading-relaxed text-muted-foreground">
            AI-powered communication overload management. Read everything,
            surface what matters.
          </p>
        </div>

        <nav aria-label="Product links">
          <h2 className="text-xs font-semibold tracking-wider text-foreground uppercase">
            Product
          </h2>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            {productLinks.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className="transition-colors hover:text-foreground"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <nav aria-label="Legal links">
          <h2 className="text-xs font-semibold tracking-wider text-foreground uppercase">
            Legal
          </h2>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            {legalLinks.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className="transition-colors hover:text-foreground"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div>
          <h2 className="text-xs font-semibold tracking-wider text-foreground uppercase">
            Contact
          </h2>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            <li>
              <a
                href={`mailto:${CONTACT_EMAIL}`}
                className="inline-flex items-center gap-2 transition-colors hover:text-foreground"
              >
                <Mail size={14} aria-hidden />
                {CONTACT_EMAIL}
              </a>
            </li>
            <li>Final Year Project — BBSUL</li>
          </ul>
        </div>
      </div>

      <div className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-6 py-5 text-xs text-muted-foreground sm:flex-row">
          <p>
            &copy; {new Date().getFullYear()} {BRAND_NAME}. Built as a Final Year
            Project.
          </p>
          <p>Policy last updated {LEGAL_LAST_UPDATED}</p>
        </div>
      </div>
    </footer>
  );
}
