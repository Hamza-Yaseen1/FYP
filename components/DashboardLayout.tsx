import AuroraBackdrop from "@/components/AuroraBackdrop";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import SignalLine from "@/components/SignalLine";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative flex h-screen overflow-hidden bg-background">
      <AuroraBackdrop />

      {/* Desktop sidebar */}
      <aside className="relative z-10 hidden w-64 shrink-0 flex-col border-r border-border/60 bg-white/60 backdrop-blur-xl lg:flex dark:bg-surface/50">
        <Sidebar />
      </aside>

      {/* Main area */}
      <div className="relative z-10 flex flex-1 flex-col overflow-hidden">
        <Navbar />
        <SignalLine />
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}