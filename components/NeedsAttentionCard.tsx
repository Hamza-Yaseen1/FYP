import { Badge } from "@/components/ui/badge";
import { timeAgo } from "@/lib/time-ago";

interface AttentionCardMessage {
  id: string;
  sender: string;
  source: string;
  created_at: string;
  ai_analysis?: {
    recommended_action?: string;
    tasks_extracted?: Array<{
      description: string;
      deadline: string | null;
      priority_indicator: string | null;
      requires_action: boolean;
    }>;
    deadlines?: string[];
    attention_reason?: string;
  };
}

export default function NeedsAttentionCard({
  message,
}: {
  message: AttentionCardMessage;
}) {
  const analysis = message.ai_analysis;
  const task = analysis?.tasks_extracted?.[0];
  const deadline = task?.deadline ?? analysis?.deadlines?.[0] ?? null;
  const sourceLabel =
    message.source.charAt(0).toUpperCase() + message.source.slice(1);

  return (
    <div className="rounded-xl border border-red-500/30 bg-card p-4 transition-colors hover:border-red-500/50">
      <div className="flex items-center justify-between gap-2">
        <Badge className="border-red-500/20 bg-red-500/15 text-[10px] font-semibold uppercase text-red-400">
          🔴 Needs Attention
        </Badge>
        <span className="shrink-0 text-xs text-muted-foreground">
          {timeAgo(message.created_at)}
        </span>
      </div>

      {task?.description && (
        <p className="mt-3 text-sm font-semibold">{task.description}</p>
      )}

      <p className="mt-1 text-xs text-muted-foreground">
        {sourceLabel} • {message.sender}
      </p>

      {deadline && (
        <p className="mt-2 text-xs">
          <span className="text-muted-foreground">Deadline: </span>
          <span className="font-medium text-red-400">{deadline}</span>
        </p>
      )}

      {analysis?.attention_reason && (
        <p className="mt-1 text-xs text-muted-foreground">
          Why it matters: {analysis.attention_reason}
        </p>
      )}

      {analysis?.recommended_action && (
        <p className="mt-1 text-xs text-blue-400">
          Recommended: {analysis.recommended_action}
        </p>
      )}
    </div>
  );
}
