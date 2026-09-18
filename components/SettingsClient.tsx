"use client";

import { useEffect, useState } from "react";
import { Bell, Shield, Trash2, User } from "lucide-react";
import { GlassCard } from "@/components/GlassCard";
import AppearanceSettings from "@/components/AppearanceSettings";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

interface Me {
  name: string;
  email: string;
}

function useLocalToggle(key: string, initial: boolean) {
  const [value, setValue] = useState(() => {
    if (typeof window === "undefined") return initial;
    const stored = window.localStorage.getItem(key);
    return stored === null ? initial : stored === "1";
  });

  const toggle = () => {
    setValue((v) => {
      const next = !v;
      window.localStorage.setItem(key, next ? "1" : "0");
      return next;
    });
  };

  return [value, toggle] as const;
}

function ToggleRow({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4 py-3">
      <div>
        <p className="text-sm font-medium">{label}</p>
        <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={onChange}
        className={`relative h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors ${
          checked ? "bg-primary" : "bg-muted-foreground/30"
        }`}
      >
        <span
          className={`absolute top-0.5 size-5 rounded-full bg-white shadow-sm transition-transform ${
            checked ? "translate-x-[22px]" : "translate-x-0.5"
          }`}
        />
      </button>
    </div>
  );
}

function SectionHeader({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof User;
  title: string;
  description: string;
}) {
  return (
    <div className="flex items-start gap-3 border-b border-border/70 px-5 py-4">
      <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-signal-dim/70 text-signal">
        <Icon size={17} strokeWidth={1.75} />
      </span>
      <div>
        <h2 className="text-sm font-semibold">{title}</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}

export default function SettingsClient() {
  const [me, setMe] = useState<Me | null>(null);
  const [emailAlerts, toggleEmailAlerts] = useLocalToggle(
    "notif.email",
    true
  );
  const [urgentAlerts, toggleUrgentAlerts] = useLocalToggle("notif.urgent", true);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiFetch<Me>("/auth/me")
      .then((data) => {
        if (!cancelled) setMe(data);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6">
      <GlassCard className="overflow-hidden">
        <SectionHeader
          icon={User}
          title="Appearance"
          description="Choose how Signal Desk looks in this browser."
        />
        <div className="p-5">
          <AppearanceSettings />
        </div>
      </GlassCard>

      <GlassCard className="overflow-hidden">
        <SectionHeader
          icon={User}
          title="Profile"
          description="Your account details, managed by the backend."
        />
        <div className="grid gap-4 p-5 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="profile-name">Full name</Label>
            <Input id="profile-name" value={me?.name ?? ""} readOnly />
          </div>
          <div className="space-y-2">
            <Label htmlFor="profile-email">Email</Label>
            <Input id="profile-email" type="email" value={me?.email ?? ""} readOnly />
          </div>
          <Button
            type="button"
            className="sm:col-span-2 w-fit rounded-full"
            onClick={() => {
              setSaved(true);
              setTimeout(() => setSaved(false), 2000);
            }}
          >
            {saved ? "Nothing to save — already synced" : "Save changes"}
          </Button>
        </div>
      </GlassCard>

      <GlassCard className="overflow-hidden">
        <SectionHeader
          icon={Bell}
          title="Notification preferences"
          description="Choose what bubbles up to your attention."
        />
        <div className="divide-y divide-border/60 px-5">
          <ToggleRow
            label="Urgent alerts"
            description="Get pinged when something needs you right now."
            checked={urgentAlerts}
            onChange={toggleUrgentAlerts}
          />
          <ToggleRow
            label="Digest emails"
            description="A calm daily summary of your most important messages."
            checked={emailAlerts}
            onChange={toggleEmailAlerts}
          />
        </div>
      </GlassCard>

      <GlassCard className="overflow-hidden">
        <SectionHeader
          icon={Shield}
          title="Account management"
          description="Sensitive actions live here."
        />
        <div className="flex flex-col gap-3 p-5 sm:flex-row">
          <Button variant="outline" className="rounded-full" type="button">
            Sign out everywhere
          </Button>
          <Button
            variant="destructive"
            className="rounded-full"
            type="button"
            title="Disabled in this build"
          >
            <Trash2 className="mr-1.5" />
            Delete account
          </Button>
        </div>
      </GlassCard>
    </div>
  );
}