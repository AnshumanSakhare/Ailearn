"""Pydantic request / response models."""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------

class VideoRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL")
    session_id: Optional[str] = None

class PDFResponse(BaseModel):
    session_id: str
    title: str
    chunks: int
    message: str

class VideoResponse(BaseModel):
    session_id: str
    title: str
    duration_seconds: Optional[int] = None
    chunks: int
    message: str


# ---------------------------------------------------------------------------
# Flashcards
# ---------------------------------------------------------------------------

class FlashcardRequest(BaseModel):
    session_id: str

class Flashcard(BaseModel):
    id: int
    front: str
    back: str
    topic: Optional[str] = None

class FlashcardsResponse(BaseModel):
    session_id: str
    flashcards: List[Flashcard]


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------

class QuizRequest(BaseModel):
    session_id: str

class QuizOption(BaseModel):
    key: str          # "A" | "B" | "C" | "D"
    text: str

class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[QuizOption]
    correct_key: str
    explanation: str

class QuizResponse(BaseModel):
    session_id: str
    questions: List[QuizQuestion]

class QuizEvalRequest(BaseModel):
    session_id: str
    answers: dict[str, str]   # {question_id: chosen_key}

class QuizEvalResult(BaseModel):
    question_id: int
    correct: bool
    correct_key: str
    explanation: str

class QuizEvalResponse(BaseModel):
    score: int
    total: int
    results: List[QuizEvalResult]


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    session_id: str
    message: str
    history: Optional[List[ChatMessage]] = []
