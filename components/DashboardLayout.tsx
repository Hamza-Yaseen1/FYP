import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import SignalLine from "@/components/SignalLine";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 border-r border-border bg-sidebar lg:block">
        <Sidebar />
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Navbar />
        <SignalLine />
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
