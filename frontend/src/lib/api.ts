/**
 * Typed API client for the FastAPI backend.
 * Base URL comes from NEXT_PUBLIC_API_URL env var.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ProcessResponse {
  session_id: string;
  title: string;
  chunks: number;
  duration_seconds?: number;
  message: string;
}

export interface Flashcard {
  id: number;
  front: string;
  back: string;
  topic?: string;
}

export interface FlashcardsResponse {
  session_id: string;
  flashcards: Flashcard[];
}

export interface QuizOption {
  key: string;
  text: string;
}

export interface QuizQuestion {
  id: number;
  question: string;
  options: QuizOption[];
  correct_key: string;
  explanation: string;
}

export interface QuizResponse {
  session_id: string;
  questions: QuizQuestion[];
}

export interface QuizEvalResult {
  question_id: number;
  correct: boolean;
  correct_key: string;
  explanation: string;
}

export interface QuizEvalResponse {
  score: number;
  total: number;
  results: QuizEvalResult[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json();
}

// ─── API Calls ────────────────────────────────────────────────────────────────

export async function processVideo(url: string, sessionId?: string): Promise<ProcessResponse> {
  return post("/process-video", { url, session_id: sessionId });
}

export async function processPDF(file: File, sessionId?: string): Promise<ProcessResponse> {
  const form = new FormData();
  form.append("file", file);
  if (sessionId) form.append("session_id", sessionId);

  const res = await fetch(`${BASE}/process-pdf`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Upload failed");
  }
  return res.json();
}

export async function generateFlashcards(sessionId: string): Promise<FlashcardsResponse> {
  return post("/generate-flashcards", { session_id: sessionId });
}

export async function generateQuiz(sessionId: string): Promise<QuizResponse> {
  return post("/generate-quiz", { session_id: sessionId });
}

export async function evaluateQuiz(
  sessionId: string,
  answers: Record<string, string>
): Promise<QuizEvalResponse> {
  return post("/generate-quiz/evaluate", { session_id: sessionId, answers });
}

/**
 * Streaming chat – returns an async generator that yields text chunks.
 */
export async function* streamChat(
  sessionId: string,
  message: string,
  history: ChatMessage[]
): AsyncGenerator<string> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message, history }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Chat failed");
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    yield decoder.decode(value, { stream: true });
  }
}
