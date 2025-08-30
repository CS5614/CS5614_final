import React, { useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import httpClient from "../services/httpClient";

type ChatRole = "user" | "assistant";
type ChatMessage = { id: string; role: ChatRole; content: string };

type ChatbotProps = {
  apiUrl?: string; // default: /api/chatbot/query
  initialAssistantMessage?: string; // Markdown OK
};

function normalizeMarkdown(md: string): string {
  const t = md?.trim() ?? "";
  const fence = "```";
  if (t.startsWith(fence) && t.endsWith(fence) && t.slice(3).includes("\n")) {
    const withoutStart = t.replace(/^```[a-zA-Z0-9_-]*\s*/, "");
    return withoutStart.replace(/\s*```$/, "").trim();
  }
  return t;
}

export default function Chatbot({
  apiUrl = "/api/chatbot/query",
  initialAssistantMessage = [
    "Hello!",
    "You’re chatting with QoLScope Assistant.",
    "",
    "How can I help you today?",
  ].join("\n"),
}: ChatbotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: "welcome", role: "assistant", content: initialAssistantMessage },
  ]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // --- textarea auto-resize helper ---
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const MAX_TEXTAREA_HEIGHT = 160; // px: ~5-7 lines，可自行調整

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, MAX_TEXTAREA_HEIGHT) + "px";
  }

  async function sendMessage() {
    const text = input.trim();
    if (!text || pending) return;

    setError(null);
    setPending(true);

    const userMsg: ChatMessage = { id: `u_${Date.now()}`, role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    // reset textarea height after clearing
    requestAnimationFrame(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    });

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const resp = await httpClient.post(
        apiUrl,
        { question: text },
        { signal: (controller as any).signal }
      );
      const data = resp?.data as { answer?: string };
      const assistantMsg: ChatMessage = {
        id: `a_${Date.now()}`,
        role: "assistant",
        content: data?.answer ?? "_(Empty response)_",
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const canceled =
        err?.code === "ERR_CANCELED" || err?.name === "AbortError" || err?.message?.includes("canceled");
      if (!canceled) {
        console.error(err);
        setError(err?.message || "Request failed");
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-4 right-4 w-14 h-14 rounded-full bg-blue-600 text-white flex items-center justify-center shadow-lg hover:bg-blue-700"
          aria-label="Open chat"
          title="Open chat"
        >
          {/* Chat bubble SVG */}
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
            <path
              d="M21 12c0 4.418-4.03 8-9 8-1.05 0-2.06-.16-3-.45L3 21l1.45-4C3.16 15.06 3 14.05 3 13 3 8.582 7.03 5 12 5s9 3.582 9 7Z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-20 right-4 w-96 h-[520px] bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-2xl shadow-xl flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-2 border-b dark:border-neutral-700">
            <span className="font-semibold">QoLScope Assistant</span>
            {/* Close button (red) */}
            <button
              onClick={() => setIsOpen(false)}
              aria-label="Close"
              title="Close"
              className="p-1 rounded !bg-red-600 !text-white hover:!bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-700 transition-colors"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path
                  d="M18 6L6 18M6 6l12 12"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((m) => (
              <MessageBubble key={m.id} msg={m} />
            ))}
            {pending && <TypingBubble />}
            {error && <div className="text-sm text-red-600">{error}</div>}
          </div>

          {/* Composer with auto-resizing textarea */}
          <div className="p-3 border-t dark:border-neutral-700 flex gap-2 items-end">
            <textarea
              ref={textareaRef}
              placeholder="Type your message... (Shift+Enter for new line)"
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                autoResize();
              }}
              onInput={autoResize}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault(); // prevent newline
                  sendMessage();
                }
              }}
              rows={1}
              className="flex-1 rounded-lg border px-3 py-2 dark:bg-neutral-800 dark:border-neutral-700 resize-none leading-6 max-h-40 overflow-y-auto"
              disabled={pending}
            />
            <button
              onClick={sendMessage}
              disabled={pending || !input.trim()}
              className="px-3 py-2 rounded-lg !bg-blue-600 !text-white hover:!bg-blue-700 disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-blue-700 transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`inline-block max-w-[320px] rounded-2xl px-4 py-2 text-sm leading-6 text-left
          ${isUser ? "bg-blue-600 text-white" : "bg-neutral-100 dark:bg-neutral-800 dark:text-neutral-100"}
          break-words whitespace-pre-wrap overflow-hidden`}  // <-- 這行是關鍵
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeSanitize]}
          components={{
            a: (props) => (
              <a {...props} target="_blank" rel="noreferrer" className="underline break-words" />
            ),
            // inline code & block code 保持原樣
            code: ({ inline, className, children, ...props }) =>
              inline ? (
                <code className="px-1 py-0.5 rounded bg-black/10 dark:bg-white/10 break-words" {...props}>
                  {children}
                </code>
              ) : (
                <pre className="overflow-x-auto rounded-lg p-3 bg-black/80 text-white text-xs">
                  <code className={className} {...props}>
                    {children}
                  </code>
                </pre>
              ),
            // 段落與列表也套用換行/斷詞
            p: (p) => <p className="mb-2 break-words whitespace-pre-wrap">{p.children}</p>,
            li: (p) => <li className="break-words whitespace-pre-wrap">{p.children}</li>,
            ul: (props) => <ul className="list-disc pl-5 space-y-1">{props.children}</ul>,
            ol: (props) => <ol className="list-decimal pl-5 space-y-1">{props.children}</ol>,
            h1: (p) => <h1 className="text-xl font-bold mb-2 break-words">{p.children}</h1>,
            h2: (p) => <h2 className="text-lg font-bold mb-2 break-words">{p.children}</h2>,
            h3: (p) => <h3 className="text-base font-bold mb-1 break-words">{p.children}</h3>,
          }}
        >
          {normalizeMarkdown(msg.content)}
        </ReactMarkdown>
      </div>
    </div>
  );
}

function TypingBubble() {
  return (
    <div className="flex w-full justify-start">
      <div className="inline-flex items-center gap-1 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-200 rounded-2xl px-3 py-2 text-sm">
        <span>Assistant is typing</span>
        <span className="inline-flex">
          <Dot />
          <Dot style={{ animationDelay: "0.15s" }} />
          <Dot style={{ animationDelay: "0.3s" }} />
        </span>
      </div>
    </div>
  );
}

function Dot(props: React.HTMLAttributes<HTMLSpanElement>) {
  return <span {...props} className="w-1.5 h-1.5 rounded-full bg-current inline-block animate-pulse" />;
}