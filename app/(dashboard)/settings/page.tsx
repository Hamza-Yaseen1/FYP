import type { Metadata } from "next";
import AppearanceSettings from "@/components/AppearanceSettings";

export const metadata: Metadata = {
  title: "Settings — Communication AI",
};

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Settings</h1>
      <p className="mt-1 text-sm text-muted-foreground">Preferences</p>

      <section className="mt-6 space-y-6">
        <div className="rounded-xl border border-border bg-card">
          <div className="border-b border-border px-5 py-4">
            <h2 className="text-sm font-semibold">Appearance</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Choose how Signal Desk looks in this browser.
            </p>
          </div>
          <div className="p-5">
            <AppearanceSettings />
          </div>
        </div>
      </section>
    </div>
  );
}