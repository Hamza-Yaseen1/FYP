import type { Metadata } from "next";
import SettingsClient from "@/components/SettingsClient";

export const metadata: Metadata = {
  title: "Settings — Communication Overload Management",
};

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Settings</h1>
      <p className="mt-1 text-sm text-muted-foreground">Preferences</p>

      <div className="mt-6">
        <SettingsClient />
      </div>
    </div>
  );
}