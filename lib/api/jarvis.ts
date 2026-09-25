import { apiFetch } from "@/lib/api";
import type { JarvisAction } from "@/components/jarvis/types";

export type { JarvisAction };

export interface JarvisChatResponse {
  reply: string;
  action: JarvisAction | null;
  used_ai: boolean;
}

export interface JarvisChatOptions {
  /** Signed token returned by a `request_confirmation` action. */
  confirmation_token?: string;
  /** Confirm (true, default) or cancel a previously requested action. */
  confirmed?: boolean;
}

export async function jarvisChat(
  message: string,
  options: JarvisChatOptions = {}
): Promise<JarvisChatResponse> {
  return apiFetch<JarvisChatResponse>("/jarvis/chat", {
    method: "POST",
    body: JSON.stringify({ message, ...options }),
  });
}