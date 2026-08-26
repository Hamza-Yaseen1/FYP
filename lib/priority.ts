export type Priority = "urgent" | "important" | "normal";

export interface PriorityConfig {
  emoji: string;
  color: string;
  bgColor: string;
}

export const priorityConfig: Record<Priority, PriorityConfig> = {
  urgent: {
    emoji: "🔴",
    color: "text-red-500",
    bgColor: "bg-red-500/15",
  },
  important: {
    emoji: "🟡",
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/15",
  },
  normal: {
    emoji: "🟢",
    color: "text-green-500",
    bgColor: "bg-green-500/15",
  },
};

export function getPriorityConfig(priority: string | null): PriorityConfig {
  if (priority && priority in priorityConfig) {
    return priorityConfig[priority as Priority];
  }
  return priorityConfig.normal;
}

export function getPriorityEmoji(priority: string | null): string {
  return getPriorityConfig(priority).emoji;
}

export function getPriorityColor(priority: string | null): string {
  return getPriorityConfig(priority).color;
}