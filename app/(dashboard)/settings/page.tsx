import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Settings — Communication AI",
};

export default function SettingsPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Manage your account settings and preferences.
      </p>
      <div className="mt-8 flex flex-col items-center justify-center rounded-xl border border-dashed py-20">
        <p className="text-sm text-muted-foreground">Settings coming soon.</p>
      </div>
    </div>
  );
}
