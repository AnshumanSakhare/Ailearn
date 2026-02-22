"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import clsx from "clsx";
import ReactMarkdown from "react-markdown";
import { ChatMessage, streamChat } from "@/lib/api";

interface Props { sessionId: string }

export default function ChatBox({ sessionId }: Props) {
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  async function send() {
    const msg = input.trim();
    if (!msg || streaming) return;
    setInput("");

    const userMsg: ChatMessage = { role: "user", content: msg };
    const assistantMsg: ChatMessage = { role: "assistant", content: "" };

    setHistory((h) => [...h, userMsg, assistantMsg]);
    setStreaming(true);

    try {
      for await (const chunk of streamChat(sessionId, msg, history)) {
        setHistory((h) => {
          const updated = [...h];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: updated[updated.length - 1].content + chunk,
          };
          return updated;
        });
      }
    } catch (err: any) {
      toast.error(err.message);
      setHistory((h) => {
        const updated = [...h];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Sorry, something went wrong. Please try again.",
        };
        return updated;
      });
    } finally {
      setStreaming(false);
      inputRef.current?.focus();
    }
  }

  return (
    <div className="flex flex-col h-[600px] card overflow-hidden animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
        <div className="flex items-center gap-2 text-slate-300">
          <Bot className="w-5 h-5 text-brand-400" />
          <span className="font-semibold">Ask about your material</span>
        </div>
        {history.length > 0 && (
          <button
            onClick={() => setHistory([])}
            className="btn-ghost text-xs px-2 py-1"
            title="Clear chat"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {history.length === 0 && (
          <div className="text-center text-slate-500 mt-12 space-y-2">
            <Bot className="w-10 h-10 mx-auto text-slate-600" />
            <p>Ask any question about your uploaded content.</p>
            <p className="text-xs text-slate-600">Responses are grounded in your material.</p>
          </div>
        )}

        {history.map((msg, i) => (
          <div
            key={i}
            className={clsx(
              "flex gap-3 animate-slide-up",
              msg.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            {msg.role === "assistant" && (
              <div className="w-8 h-8 rounded-full bg-brand-700 flex items-center justify-center shrink-0 mt-1">
                <Bot className="w-4 h-4 text-white" />
              </div>
            )}
            <div
              className={clsx(
                "max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed",
                msg.role === "user"
                  ? "bg-brand-600 text-white rounded-tr-sm"
                  : "bg-slate-700 text-slate-100 rounded-tl-sm"
              )}
            >
              {msg.role === "assistant" ? (
                <ReactMarkdown
                  components={{
                    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                    code: ({ children }) => (
                      <code className="bg-slate-900 px-1 py-0.5 rounded text-brand-300 text-xs">
                        {children}
                      </code>
                    ),
                    ul: ({ children }) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
                    li: ({ children }) => <li className="mb-1">{children}</li>,
                  }}
                >
                  {msg.content || (streaming && i === history.length - 1 ? "▋" : "")}
                </ReactMarkdown>
              ) : (
                msg.content
              )}
            </div>
            {msg.role === "user" && (
              <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center shrink-0 mt-1">
                <User className="w-4 h-4 text-slate-300" />
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-slate-700 p-3 flex gap-2">
        <input
          ref={inputRef}
          className="input flex-1"
          placeholder="Ask a question…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          disabled={streaming}
          autoFocus
        />
        <button onClick={send} disabled={streaming || !input.trim()} className="btn-primary px-4">
          {streaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </div>
    </div>
  );
}
