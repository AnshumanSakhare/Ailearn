"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, RotateCcw, Loader2, Tag } from "lucide-react";
import toast from "react-hot-toast";
import { Flashcard, generateFlashcards } from "@/lib/api";
import clsx from "clsx";

interface Props {
  sessionId: string;
}

export default function FlashcardDeck({ sessionId }: Props) {
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const res = await generateFlashcards(sessionId);
      setCards(res.flashcards);
      setIndex(0);
      setFlipped(false);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }

  function prev() { setIndex((i) => Math.max(0, i - 1)); setFlipped(false); }
  function next() { setIndex((i) => Math.min(cards.length - 1, i + 1)); setFlipped(false); }

  const card = cards[index];

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-200">Flashcards</h2>
        <button onClick={load} disabled={loading} className="btn-ghost text-sm">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
          {cards.length ? "Regenerate" : "Generate"}
        </button>
      </div>

      {!cards.length && !loading && (
        <div className="card p-12 text-center text-slate-500">
          <p>Click <strong className="text-slate-400">Generate</strong> to create flashcards from your material.</p>
        </div>
      )}

      {loading && (
        <div className="card p-12 flex items-center justify-center gap-3 text-slate-400">
          <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
          <span>Generating {12} flashcards…</span>
        </div>
      )}

      {card && !loading && (
        <>
          {/* Progress */}
          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>Card {index + 1} of {cards.length}</span>
            {card.topic && (
              <span className="flex items-center gap-1 text-brand-400">
                <Tag className="w-3 h-3" /> {card.topic}
              </span>
            )}
          </div>

          {/* Progress bar */}
          <div className="h-1 bg-slate-700 rounded-full">
            <div
              className="h-1 bg-brand-500 rounded-full transition-all duration-300"
              style={{ width: `${((index + 1) / cards.length) * 100}%` }}
            />
          </div>

          {/* Card */}
          <div
            onClick={() => setFlipped((f) => !f)}
            className={clsx(
              "card p-8 min-h-[200px] flex flex-col items-center justify-center text-center",
              "cursor-pointer select-none transition-all duration-300 hover:border-brand-500",
              flipped ? "bg-brand-900/30 border-brand-700" : ""
            )}
          >
            <span className="text-xs uppercase tracking-widest text-slate-500 mb-4">
              {flipped ? "Answer" : "Question"}
            </span>
            <p className="text-lg font-medium text-slate-100 leading-relaxed">
              {flipped ? card.back : card.front}
            </p>
            <p className="text-xs text-slate-600 mt-6">Click to {flipped ? "see question" : "reveal answer"}</p>
          </div>

          {/* Navigation */}
          <div className="flex gap-3 justify-center">
            <button onClick={prev} disabled={index === 0} className="btn-ghost">
              <ChevronLeft className="w-4 h-4" /> Prev
            </button>
            <button onClick={next} disabled={index === cards.length - 1} className="btn-ghost">
              Next <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </>
      )}
    </div>
  );
}
