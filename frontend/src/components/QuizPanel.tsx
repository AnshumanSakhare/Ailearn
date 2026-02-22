"use client";

import { useState } from "react";
import {
  Loader2, RotateCcw, CheckCircle2, XCircle, Trophy, RefreshCw,
} from "lucide-react";
import toast from "react-hot-toast";
import clsx from "clsx";
import {
  QuizQuestion, QuizEvalResult,
  generateQuiz, evaluateQuiz,
} from "@/lib/api";

interface Props { sessionId: string }

type Phase = "idle" | "loading" | "quiz" | "submitting" | "results";

export default function QuizPanel({ sessionId }: Props) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [results, setResults] = useState<QuizEvalResult[]>([]);
  const [score, setScore] = useState(0);

  async function load() {
    setPhase("loading");
    setAnswers({});
    setResults([]);
    try {
      const res = await generateQuiz(sessionId);
      setQuestions(res.questions);
      setPhase("quiz");
    } catch (err: any) {
      toast.error(err.message);
      setPhase("idle");
    }
  }

  async function submit() {
    if (Object.keys(answers).length < questions.length) {
      toast.error("Please answer all questions first.");
      return;
    }
    setPhase("submitting");
    try {
      const res = await evaluateQuiz(sessionId, answers);
      setResults(res.results);
      setScore(res.score);
      setPhase("results");
    } catch (err: any) {
      toast.error(err.message);
      setPhase("quiz");
    }
  }

  const resultMap = Object.fromEntries(results.map((r) => [r.question_id, r]));

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-200">Quiz</h2>
        <button onClick={load} disabled={phase === "loading"} className="btn-ghost text-sm">
          {phase === "loading"
            ? <Loader2 className="w-4 h-4 animate-spin" />
            : <RotateCcw className="w-4 h-4" />
          }
          {questions.length ? "New Quiz" : "Generate"}
        </button>
      </div>

      {phase === "idle" && (
        <div className="card p-12 text-center text-slate-500">
          <p>Click <strong className="text-slate-400">Generate</strong> to create a quiz.</p>
        </div>
      )}

      {phase === "loading" && (
        <div className="card p-12 flex items-center justify-center gap-3 text-slate-400">
          <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
          <span>Generating quiz questions…</span>
        </div>
      )}

      {/* Results summary */}
      {phase === "results" && (
        <div className="card p-6 flex items-center gap-4 bg-slate-800">
          <Trophy className="w-10 h-10 text-yellow-400 shrink-0" />
          <div>
            <p className="font-bold text-2xl text-white">{score}/{questions.length}</p>
            <p className="text-slate-400 text-sm">
              {Math.round((score / questions.length) * 100)}% correct ·{" "}
              {score === questions.length ? "Perfect! 🎉" : score > questions.length / 2 ? "Good job!" : "Keep practising!"}
            </p>
          </div>
          <button onClick={load} className="btn-ghost ml-auto text-sm">
            <RefreshCw className="w-4 h-4" /> Retake
          </button>
        </div>
      )}

      {/* Questions */}
      {(phase === "quiz" || phase === "submitting" || phase === "results") &&
        questions.map((q) => {
          const res = resultMap[q.id];
          const chosen = answers[String(q.id)];
          return (
            <div key={q.id} className="card p-5 space-y-4">
              <p className="font-medium text-slate-100">
                <span className="text-brand-400 mr-2">{q.id}.</span>
                {q.question}
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {q.options.map((opt) => {
                  const isChosen = chosen === opt.key;
                  const isCorrect = opt.key === q.correct_key;
                  const revealed = !!res;

                  return (
                    <button
                      key={opt.key}
                      disabled={phase !== "quiz"}
                      onClick={() =>
                        setAnswers((a) => ({ ...a, [String(q.id)]: opt.key }))
                      }
                      className={clsx(
                        "text-left px-4 py-3 rounded-xl border text-sm transition-all duration-200",
                        {
                          // Default
                          "border-slate-700 bg-slate-900/60 hover:border-brand-500 text-slate-300":
                            !isChosen && !revealed,
                          // Chosen, not yet evaluated
                          "border-brand-500 bg-brand-900/30 text-brand-200":
                            isChosen && !revealed,
                          // Revealed correct
                          "border-green-500 bg-green-900/30 text-green-300":
                            revealed && isCorrect,
                          // Revealed wrong chosen
                          "border-red-500 bg-red-900/30 text-red-300":
                            revealed && isChosen && !isCorrect,
                          // Revealed not chosen, not correct
                          "border-slate-700 bg-slate-900/40 text-slate-500":
                            revealed && !isChosen && !isCorrect,
                        }
                      )}
                    >
                      <span className="font-bold mr-2">{opt.key}.</span>
                      {opt.text}
                    </button>
                  );
                })}
              </div>

              {/* Explanation after evaluation */}
              {res && (
                <div className={clsx(
                  "flex items-start gap-2 text-sm p-3 rounded-lg",
                  res.correct ? "bg-green-900/20 text-green-300" : "bg-red-900/20 text-red-300"
                )}>
                  {res.correct
                    ? <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                    : <XCircle className="w-4 h-4 shrink-0 mt-0.5" />}
                  <p>{res.explanation}</p>
                </div>
              )}
            </div>
          );
        })
      }

      {phase === "quiz" && questions.length > 0 && (
        <button onClick={submit} className="btn-primary w-full justify-center">
          Submit Quiz
        </button>
      )}

      {phase === "submitting" && (
        <div className="btn-primary w-full justify-center opacity-75 pointer-events-none">
          <Loader2 className="w-4 h-4 animate-spin" /> Evaluating…
        </div>
      )}
    </div>
  );
}
