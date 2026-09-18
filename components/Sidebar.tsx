"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Inbox,
  AlertTriangle,
  BarChart3,
  CheckSquare,
  Link2,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
  { icon: Inbox, label: "Inbox", href: "/inbox" },
  { icon: AlertTriangle, label: "Attention", href: "/attention" },
  { icon: BarChart3, label: "Analytics", href: "/analytics" },
  { icon: CheckSquare, label: "Tasks", href: "/tasks" },
  { icon: Link2, label: "Connections", href: "/connections" },
  { icon: Settings, label: "Settings", href: "/settings" },
];

interface SidebarProps {
  className?: string;
  onNavigate?: () => void;
}

export default function Sidebar({ className, onNavigate }: SidebarProps) {
  const pathname = usePathname();

  return (
    <div className={cn("flex h-full flex-col", className)}>
{/* Brand */}
      <div className="flex items-center gap-3 px-5 pt-6 pb-5">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-linear-to-br from-signal to-violet-400 text-sm font-semibold text-primary-foreground shadow-md shadow-signal/25">
          S
        </span>
        <div className="leading-tight">
          <span className="block text-[15px] font-semibold tracking-tight">
            Signal Desk
          </span>
          <span className="text-xs text-muted-foreground">
            Communication overload, managed
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-0.5 px-3 py-2">
        <p className="triage-label px-3 pb-2 pt-1 text-muted-foreground/70">
          Menu
        </p>
        {navItems.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "group flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-signal-dim/60 text-foreground ring-1 ring-signal/15"
                  : "text-muted-foreground hover:bg-accent/70 hover:text-foreground"
              )}
            >
              <item.icon
                size={17}
                className={cn(
                  "shrink-0 transition-colors",
                  isActive
                    ? "text-primary"
                    : "text-muted-foreground/70 group-hover:text-foreground"
                )}
              />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-border px-5 py-4">
        <p className="triage-label text-muted-foreground/60">v1.0.0</p>
      </div>
    </div>
  );
}