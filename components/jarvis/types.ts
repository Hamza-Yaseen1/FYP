export type JarvisOrbState = "idle" | "listening" | "thinking" | "speaking";

export type JarvisActionType =
  | "navigation"
  | "request_confirmation"
  | "create_task"
  | "complete_task"
  | "delete_task"
  | "list_completed_tasks"
  | "list_important_messages"
  | "summarize_messages"
  | "search_messages"
  | "analyze_attention"
  | "explain_attention"
  | "draft_reply"
  | "get_data";

export interface JarvisAction {
  type: JarvisActionType;
  target?: string | null;
  detail?: Record<string, unknown> | null;
  confirmation_token?: string | null;
}

export interface JarvisMessage {
  role: "user" | "assistant";
  text: string;
  action?: JarvisAction | null;
}