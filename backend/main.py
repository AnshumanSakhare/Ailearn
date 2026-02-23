"""
AI Learning Assistant – FastAPI Backend
Entry point: uvicorn main:app --reload
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import video, pdf, flashcards, quiz, chat
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log config at startup so Railway logs confirm env vars are loaded
logger.info("GEMINI_API_KEY loaded: %s", bool(settings.GEMINI_API_KEY))
logger.info("EMBEDDING_MODEL: %s", settings.EMBEDDING_MODEL)
logger.info("CHAT_MODEL: %s", settings.CHAT_MODEL)

app = FastAPI(
    title="AI Learning Assistant API",
    version="1.0.0",
    description="Process YouTube videos & PDFs → flashcards, quizzes, and RAG chat.",
)

# ---------------------------------------------------------------------------
# CORS – allow Next.js dev server and production domain
# ---------------------------------------------------------------------------
# Always include common localhost origins so dev never breaks
_origins = list(set(settings.CORS_ORIGINS + [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    # Production Vercel frontend – hardcoded as fallback in case FRONTEND_URL env var is missing
    "https://ailearn-five.vercel.app",
] + ([settings.FRONTEND_URL.rstrip("/")] if settings.FRONTEND_URL else [])))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
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
    return {
        "status": "ok",
        "gemini_key_set": bool(settings.GEMINI_API_KEY),
        "embedding_model": settings.EMBEDDING_MODEL,
        "chat_model": settings.CHAT_MODEL,
    }


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
