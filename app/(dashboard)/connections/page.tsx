import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Connections — Communication AI",
};

export default function ConnectionsPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold tracking-tight">Connections</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Manage your connected accounts and integrations.
      </p>
      <div className="mt-8 flex flex-col items-center justify-center rounded-xl border border-dashed py-20">
        <p className="text-sm text-muted-foreground">No connections configured.</p>
      </div>
    </div>
  );
}
