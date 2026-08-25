import { AlertTriangle, ArrowRight, Clock, Mail, MessageCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useTimeAgo } from "@/lib/use-time-ago";

interface AttentionCardMessage {
  id: string;
  sender: string;
  source: string;
  content?: string;
  created_at: string;
  ai_analysis?: {
    summary?: string;
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

const sourceIcons: Record<string, typeof Mail> = {
  whatsapp: MessageCircle,
  gmail: Mail,
};

export default function NeedsAttentionCard({
  message,
}: {
  message: AttentionCardMessage;
}) {
  const analysis = message.ai_analysis;
  const task = analysis?.tasks_extracted?.[0];
  const deadline = task?.deadline ?? analysis?.deadlines?.[0] ?? null;
  const timeLabel = useTimeAgo(message.created_at);
  const sourceLabel =
    message.source.charAt(0).toUpperCase() + message.source.slice(1);
  const SourceIcon = sourceIcons[message.source.toLowerCase()];
  const title =
    task?.description ?? analysis?.summary ?? message.content ?? "";

  return (
    <div className="overflow-hidden rounded-xl border border-red-500/25 bg-card transition-colors hover:border-red-500/50">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between gap-2">
          <Badge className="gap-1 border-red-500/25 bg-red-500/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-red-400">
            <AlertTriangle className="size-3" aria-hidden />
            Needs Attention
          </Badge>
          <span className="shrink-0 text-xs text-muted-foreground">
            {timeLabel}
          </span>
        </div>

        {/* Task title */}
        {title && (
          <h3 className="mt-3 text-sm font-semibold leading-snug">{title}</h3>
        )}

        {/* Source + sender */}
        <p className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
          {SourceIcon && (
            <SourceIcon className="size-3.5 shrink-0" aria-hidden />
          )}
          <span>
            {sourceLabel} • {message.sender}
          </span>
        </p>

        {/* Deadline */}
        {deadline && (
          <div className="mt-3 inline-flex max-w-full items-center gap-1.5 rounded-md border border-red-500/25 bg-red-500/10 px-2 py-1">
            <Clock className="size-3.5 shrink-0 text-red-400" aria-hidden />
            <span className="truncate text-xs text-red-300">
              <span className="font-semibold">Deadline:</span> {deadline}
            </span>
          </div>
        )}

        {/* Why it matters */}
        {analysis?.attention_reason && (
          <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
            <span className="font-medium text-foreground/80">
              Why it matters:{" "}
            </span>
            {analysis.attention_reason}
          </p>
        )}

        {/* Recommended action */}
        {analysis?.recommended_action && (
          <div className="mt-3 rounded-lg border border-blue-500/20 bg-blue-500/[0.07] p-3">
            <p className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-blue-400">
              <ArrowRight className="size-3" aria-hidden />
              Recommended Action
            </p>
            <p className="mt-1 text-xs leading-relaxed text-blue-100/90">
              {analysis.recommended_action}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
