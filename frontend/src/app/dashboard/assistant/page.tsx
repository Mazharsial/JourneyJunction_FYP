"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";
import { chatApi } from "@/lib/chat-api";

interface Msg {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTIONS = [
  "Do I need a visa for Dubai from Pakistan?",
  "Suggest hotels in Dubai",
  "What's the best time to visit Dubai?",
  "Help me plan a 5-day trip to Dubai",
];

export default function AssistantPage() {
  const { authCall } = useAuth();
  const [messages, setMessages] = useState<Msg[]>([
    { role: "assistant", content: "Hi! I'm your Journey Junction travel assistant. Ask me about visas, flights, hotels or planning a trip." },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [convoId, setConvoId] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function send(text: string) {
    const message = text.trim();
    if (!message || sending) return;
    setError(null);
    setInput("");
    setMessages((m) => [...m, { role: "user", content: message }]);
    setSending(true);
    try {
      const res = await authCall((t) => chatApi.send(t, message, convoId));
      setConvoId(res.conversation_id);
      setMessages((m) => [...m, { role: "assistant", content: res.reply.content }]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The assistant is unavailable right now.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-10rem)] max-w-3xl flex-col">
      <h1 className="text-2xl font-bold text-foreground">AI travel assistant</h1>
      <p className="mt-1 text-sm text-muted">Grounded answers on visas, flights, hotels and planning.</p>

      <div className="mt-4 flex-1 space-y-4 overflow-y-auto rounded-2xl border border-border bg-surface p-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm ${
                m.role === "user"
                  ? "brand-gradient text-white"
                  : "border border-border bg-surface-muted text-foreground"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex justify-start">
            <div className="flex gap-1 rounded-2xl border border-border bg-surface-muted px-4 py-3">
              <span className="h-2 w-2 animate-bounce rounded-full bg-muted [animation-delay:-0.2s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-muted [animation-delay:-0.1s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-muted" />
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {messages.length <= 1 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="rounded-full border border-border bg-surface px-3 py-1.5 text-xs text-muted transition hover:bg-surface-muted hover:text-foreground"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {error && <p className="mt-2 text-xs text-error">{error}</p>}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void send(input);
        }}
        className="mt-3 flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about visas, flights, hotels…"
          className="flex-1 rounded-xl border border-border bg-surface px-4 py-2.5 text-sm text-foreground outline-none focus:border-teal focus:ring-2 focus:ring-teal/30"
        />
        <Button type="submit" loading={sending} disabled={!input.trim()}>
          Send
        </Button>
      </form>
    </div>
  );
}
