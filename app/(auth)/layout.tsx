import ThemeToggle from "@/components/ThemeToggle";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative flex min-h-screen flex-col bg-background px-4">
      {/* Theme toggle */}
      <div className="flex justify-end pb-2 pt-4 sm:pt-6">
        <ThemeToggle />
      </div>

      <div className="flex flex-1 items-center justify-center pb-16">
        <div className="w-full max-w-sm">
          {/* Brand */}
          <div className="mb-8 flex flex-col items-center gap-4">
            <div className="flex size-12 items-center justify-center rounded-2xl bg-primary text-lg font-semibold text-primary-foreground">
              S
            </div>
            <div className="text-center">
              <h1 className="text-2xl font-semibold tracking-tight">
                Signal Desk
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Communication triage, sorted by AI
              </p>
            </div>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}