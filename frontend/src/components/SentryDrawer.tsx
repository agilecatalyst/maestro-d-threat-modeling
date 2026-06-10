import { useEffect, useRef, useState } from "react";
import { clearSentrySession, sendSentryMessage } from "../api/sentryClient";
import type { ThreatModelResult } from "../types";

type ChatMessage = {
  role: "user" | "assistant";
  text: string;
};

type Props = {
  open: boolean;
  threatModelId: string;
  model: ThreatModelResult;
  onClose: () => void;
  onCatalogChanged: () => void;
};

export function SentryDrawer({ open, threatModelId, model, onClose, onCatalogChanged }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open && messages.length === 0) {
      setMessages([
        {
          role: "assistant",
          text: "I'm Sentry — ask about gaps, mitigations, or tell me to add or refine threats.",
        },
      ]);
    }
  }, [open, messages.length]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  if (!open) return null;

  const send = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setError(null);
    setBusy(true);
    setMessages((prev) => [...prev, { role: "user", text }]);
    try {
      const payload = await sendSentryMessage(threatModelId, text, model);
      setMessages((prev) => [...prev, { role: "assistant", text: payload.reply ?? "Done." }]);
      if ((payload.tools_used?.length ?? 0) > 0) {
        onCatalogChanged();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sentry failed");
    } finally {
      setBusy(false);
    }
  };

  const handleClear = async () => {
    await clearSentrySession(threatModelId);
    setMessages([
      {
        role: "assistant",
        text: "Session cleared. What would you like to explore?",
      },
    ]);
  };

  return (
    <aside className="sentry-drawer" aria-label="Sentry assistant">
      <div className="sentry-header">
        <div>
          <strong>Sentry</strong>
          <p className="subtitle" style={{ margin: 0 }}>AI security assistant</p>
        </div>
        <div className="actions-row" style={{ margin: 0 }}>
          <button type="button" className="btn btn-ghost" onClick={() => void handleClear()}>
            Clear
          </button>
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Close
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="sentry-messages" ref={listRef}>
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`sentry-message ${message.role === "user" ? "user" : "assistant"}`}
          >
            {message.text}
          </div>
        ))}
        {busy && (
          <div className="sentry-message assistant">
            <div className="spinner" style={{ display: "inline-block", verticalAlign: "middle" }} />
            {" "}Thinking…
          </div>
        )}
      </div>

      <div className="sentry-input-row">
        <textarea
          rows={2}
          placeholder="Ask Sentry about threats, gaps, or mitigations…"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void send();
            }
          }}
        />
        <button type="button" className="btn btn-primary" disabled={busy} onClick={() => void send()}>
          Send
        </button>
      </div>
    </aside>
  );
}
