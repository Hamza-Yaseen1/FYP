import { Clock, Mail, MessageCircle } from "lucide-react";
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

const pillBase =
  "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium leading-4";

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
    <div className="overflow-hidden rounded-xl border border-ember/20 bg-card transition-colors hover:border-ember/40">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between gap-2">
          <Badge
            variant="outline"
            className={`${pillBase} border-ember/25 bg-ember/10 text-ember`}
          >
            Needs attention
          </Badge>
          <span className="shrink-0 font-mono text-[11px] text-muted-foreground">
            {timeLabel}
          </span>
        </div>

        {/* Task title */}
        {title && (
          <h3 className="mt-3 text-base font-semibold leading-snug tracking-tight">
            {title}
          </h3>
        )}

        {/* Source + sender */}
        <p className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
          {SourceIcon && (
            <SourceIcon className="size-3.5 shrink-0" aria-hidden />
          )}
          <span>
            {sourceLabel} · {message.sender}
          </span>
        </p>

        {/* Deadline */}
        {deadline && (
          <div className="mt-3 inline-flex max-w-full items-center gap-1.5 rounded-full border border-ember/25 bg-ember/10 px-2 py-0.5">
            <Clock className="size-3.5 shrink-0 text-ember" aria-hidden />
            <span className="truncate font-mono text-[11px] font-medium text-ember">
              by {deadline}
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
          <div className="mt-3 rounded-lg bg-muted/60 p-3">
            <p className="triage-label text-primary">Recommended action</p>
            <p className="mt-1 text-xs leading-relaxed text-foreground/90">
              {analysis.recommended_action}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}