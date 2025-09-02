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
  // 用 trimEnd() 移除字串尾端多餘的換行/空白（解決訊息最後多一個換行）
  const t = (md ?? "").trimEnd();
  const fence = "```";
  if (t.startsWith(fence) && t.endsWith(fence) && t.slice(3).includes("\n")) {
    const withoutStart = t.replace(/^```[a-zA-Z0-9_-]*\s*/, "");
    // 這裡也用 trimEnd()，避免程式碼區塊結尾多出空行
    return withoutStart.replace(/\s*```$/, "").trimEnd();
  }
  return t;
}

export default function Chatbot({
  apiUrl = "/api/chatbot/query",
  initialAssistantMessage = [
    "Hello!",
    "You’re chatting with QoLScope Assistant.",
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
          style={{ backgroundColor: "#1E3050" }}
        >
          {/* Chat bubble SVG */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="32"
            height="32"
            viewBox="0 0 640 640">
          <path fill="#ffffff" d="M64 304C64 358.4 83.3 408.6 115.9 448.9L67.1 538.3C65.1 542 64 546.2 64 550.5C64 564.6 75.4 576 89.5 576C93.5 576 97.3 575.4 101 573.9L217.4 524C248.8 536.9 283.5 544 320 544C461.4 544 576 436.5 576 304C576 171.5 461.4 64 320 64C178.6 64 64 171.5 64 304zM158 471.9C167.3 454.8 165.4 433.8 153.2 418.7C127.1 386.4 112 346.8 112 304C112 200.8 202.2 112 320 112C437.8 112 528 200.8 528 304C528 407.2 437.8 496 320 496C289.8 496 261.3 490.1 235.7 479.6C223.8 474.7 210.4 474.8 198.6 479.9L140 504.9L158 471.9zM208 336C225.7 336 240 321.7 240 304C240 286.3 225.7 272 208 272C190.3 272 176 286.3 176 304C176 321.7 190.3 336 208 336zM352 304C352 286.3 337.7 272 320 272C302.3 272 288 286.3 288 304C288 321.7 302.3 336 320 336C337.7 336 352 321.7 352 304zM432 336C449.7 336 464 321.7 464 304C464 286.3 449.7 272 432 272C414.3 272 400 286.3 400 304C400 321.7 414.3 336 432 336z"/>
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
              placeholder="Type your message..."
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
            code: (props) => {
              const { inline, className, children, ...rest } = props as any;
              return inline ? (
                <code className="px-1 py-0.5 rounded bg-black/10 dark:bg-white/10 break-words" {...rest}>
                  {children}
                </code>
              ) : (
                <pre className="overflow-x-auto rounded-lg p-3 bg-black/80 text-white text-xs">
                  <code className={className} {...rest}>
                    {children}
                  </code>
                </pre>
              );
            },
            // 段落與列表也套用換行/斷詞
            p: (p) => <p className="mb-2 last:mb-0 break-words whitespace-pre-wrap">{p.children}</p>,
            li: (p) => <li className="break-words whitespace-pre-wrap">{p.children}</li>,
            ul: (props) => <ul className="list-disc pl-5 space-y-1 last:mb-0">{props.children}</ul>,
            ol: (props) => <ol className="list-decimal pl-5 space-y-1 last:mb-0">{props.children}</ol>,
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