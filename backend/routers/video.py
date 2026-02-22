"""POST /process-video – ingest a YouTube video."""

import uuid
from fastapi import APIRouter, HTTPException

from models.schemas import VideoRequest, VideoResponse
from services.youtube import fetch_transcript
from services.embeddings import chunk_text, embed_texts
from services.vector_store import upsert_chunks
from services.session_store import set_session
from config import settings

router = APIRouter()


@router.post("", response_model=VideoResponse)
async def process_video(body: VideoRequest):
    session_id = body.session_id or str(uuid.uuid4())

    try:
        title, transcript, duration = await fetch_transcript(body.url)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Transcript error: {exc}")

    if not transcript.strip():
        raise HTTPException(status_code=422, detail="Empty transcript returned for this video.")

    # Chunk + embed
    chunks = chunk_text(transcript)
    if not chunks:
        raise HTTPException(status_code=422, detail="Could not chunk transcript.")

    embeddings = await embed_texts(chunks)
    upsert_chunks(session_id, chunks, embeddings)

    # Persist metadata for downstream endpoints
    set_session(session_id, {
        "title": title,
        "source_type": "video",
        "url": body.url,
        "chunks": chunks,
        "full_text": transcript,
    })

    return VideoResponse(
        session_id=session_id,
        title=title,
        duration_seconds=duration,
        chunks=len(chunks),
        message="Video processed successfully. You can now generate flashcards, quiz, or chat.",
    )
