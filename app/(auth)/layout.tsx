import { Inbox } from "lucide-react";
import AuroraBackdrop from "@/components/AuroraBackdrop";
import { GlassCard } from "@/components/GlassCard";
import ThemeToggle from "@/components/ThemeToggle";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-background px-4">
      <AuroraBackdrop />

      {/* Theme toggle */}
      <div className="relative z-10 flex justify-end pb-2 pt-4 sm:pt-6">
        <ThemeToggle />
      </div>

      <div className="relative z-10 flex flex-1 items-center justify-center pb-14">
        <div className="w-full max-w-md">
          <GlassCard className="p-6 sm:p-8">
            {/* Brand */}
            <div className="mb-7 flex flex-col items-center gap-3">
              <div className="flex size-12 items-center justify-center rounded-2xl bg-linear-to-br from-signal to-violet-400 text-primary-foreground shadow-lg shadow-signal/25">
                <Inbox size={22} strokeWidth={2} />
              </div>
              <div className="text-center">
                <h1 className="text-xl font-semibold tracking-tight">
                  Signal Desk
                </h1>
                <p className="mt-1 text-sm text-muted-foreground">
                  Communication triage, sorted by AI
                </p>
              </div>
            </div>
            {children}
          </GlassCard>
          <p className="mt-6 text-center text-xs text-muted-foreground">
            Built as Final Year Project – BBSUL
          </p>
        </div>
      </div>
    </div>
  );
}