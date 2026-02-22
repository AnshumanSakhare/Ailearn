"use client";

import { useState } from "react";
import { BookOpen, HelpCircle, MessageSquare, Sparkles } from "lucide-react";
import clsx from "clsx";

import Navbar from "@/components/Navbar";
import SourceInput from "@/components/SourceInput";
import FlashcardDeck from "@/components/FlashcardDeck";
import QuizPanel from "@/components/QuizPanel";
import ChatBox from "@/components/ChatBox";
import { ProcessResponse } from "@/lib/api";

type Tab = "flashcards" | "quiz" | "chat";

const tabs: { id: Tab; label: string; icon: React.FC<any> }[] = [
  { id: "flashcards", label: "Flashcards", icon: BookOpen },
  { id: "quiz",       label: "Quiz",       icon: HelpCircle },
  { id: "chat",       label: "Chat",       icon: MessageSquare },
];

export default function Home() {
  const [session, setSession] = useState<ProcessResponse | null>(null);
  const [tab, setTab] = useState<Tab>("flashcards");
  const [loading, setLoading] = useState(false);

  function handleProcessed(res: ProcessResponse) {
    setSession(res);
    setTab("flashcards");
  }

  return (
    <div className="min-h-screen bg-slate-900">
      <Navbar title={session?.title} />

      <main className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-10 space-y-8">

        {/* Hero */}
        {!session && (
          <div className="text-center space-y-3 py-8 animate-fade-in">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-brand-900/60 border border-brand-700 rounded-full text-brand-300 text-sm mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              Powered by GPT-4o + RAG
            </div>
            <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">
              Learn Smarter with AI
            </h1>
            <p className="text-slate-400 max-w-xl mx-auto text-lg">
              Upload a YouTube video or PDF. Instantly get flashcards, a quiz,
              and an AI chat assistant grounded in your content.
            </p>
          </div>
        )}

        {/* Source Input */}
        <div className={clsx("max-w-2xl", session ? "mx-auto" : "mx-auto")}>
          <SourceInput
            onProcessed={handleProcessed}
            loading={loading}
            setLoading={setLoading}
          />
        </div>

        {/* Post-process panels */}
        {session && (
          <div className="space-y-6 animate-slide-up">
            {/* Session badge */}
            <div className="flex flex-wrap items-center gap-3 text-sm text-slate-400">
              <span className="px-3 py-1 bg-slate-800 border border-slate-700 rounded-full">
                📌 {session.title}
              </span>
              <span className="px-3 py-1 bg-slate-800 border border-slate-700 rounded-full">
                {session.chunks} chunks indexed
              </span>
              {session.duration_seconds && (
                <span className="px-3 py-1 bg-slate-800 border border-slate-700 rounded-full">
                  ⏱ {Math.round(session.duration_seconds / 60)} min video
                </span>
              )}
            </div>

            {/* Tab bar */}
            <div className="flex gap-2 flex-wrap">
              {tabs.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setTab(id)}
                  className={clsx(
                    "tab-btn flex items-center gap-2",
                    tab === id ? "tab-active" : "tab-inactive"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div>
              {tab === "flashcards" && <FlashcardDeck sessionId={session.session_id} />}
              {tab === "quiz"       && <QuizPanel     sessionId={session.session_id} />}
              {tab === "chat"       && <ChatBox       sessionId={session.session_id} />}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 mt-16 py-6 text-center text-slate-600 text-sm">
        AI Learning Assistant · Built with Next.js, FastAPI & OpenAI
      </footer>
    </div>
  );
}
