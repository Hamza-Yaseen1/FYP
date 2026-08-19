import { Zap } from "lucide-react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm space-y-6">
        {/* Logo */}
        <div className="flex flex-col items-center gap-2">
          <div className="flex size-10 items-center justify-center rounded-xl bg-primary">
            <Zap size={20} className="text-primary-foreground" />
          </div>
          <h1 className="text-xl font-semibold tracking-tight">
            Communication AI
          </h1>
        </div>
        {children}
      </div>
    </div>
  );
}
