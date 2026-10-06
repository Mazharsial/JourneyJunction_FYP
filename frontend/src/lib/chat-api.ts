/** Typed client for the AI assistant endpoints. */
import { apiFetch } from "@/lib/api";

export interface ChatMessageOut {
  id: string;
  role: "user" | "assistant";
  content: string;
  meta: Record<string, unknown>;
  created_at: string;
}

export interface ChatSource {
  label: string;
  url: string;
}

export interface ChatResponse {
  conversation_id: string;
  reply: ChatMessageOut;
  intent: string;
  status: "ok" | "fallback";
  sources: ChatSource[];
  suggestions: string[];
}

export const chatApi = {
  send: (token: string, message: string, conversationId?: string) =>
    apiFetch<ChatResponse>("/chat", {
      method: "POST",
      token,
      body: { message, conversation_id: conversationId ?? null },
    }),
};
