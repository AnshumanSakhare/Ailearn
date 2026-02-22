"""
AI Learning Assistant – FastAPI Backend
Entry point: uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import video, pdf, flashcards, quiz, chat
from config import settings

app = FastAPI(
    title="AI Learning Assistant API",
    version="1.0.0",
    description="Process YouTube videos & PDFs → flashcards, quizzes, and RAG chat.",
)

# ---------------------------------------------------------------------------
# CORS – allow Next.js dev server and production domain
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(video.router,      prefix="/process-video",    tags=["Ingest"])
app.include_router(pdf.router,        prefix="/process-pdf",      tags=["Ingest"])
app.include_router(flashcards.router, prefix="/generate-flashcards", tags=["Generate"])
app.include_router(quiz.router,       prefix="/generate-quiz",    tags=["Generate"])
app.include_router(chat.router,       prefix="/chat",             tags=["Chat"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
