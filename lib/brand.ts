export const BRAND_NAME = "Sift";
export const ASSISTANT_NAME = "Kestrel";

export function localizeAssistantReply(text: string): string {
  if (!text) return text;
  return text
    .replace(/\bJARVIS\b/gi, ASSISTANT_NAME)
    .replace(/\bSignal\s+Desk\b/gi, BRAND_NAME);
}
