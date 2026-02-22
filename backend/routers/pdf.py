"""POST /process-pdf – ingest an uploaded PDF."""

import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from models.schemas import PDFResponse
from services.pdf import extract_pdf_text
from services.embeddings import chunk_text, embed_texts
from services.vector_store import upsert_chunks
from services.session_store import set_session

router = APIRouter()

MAX_PDF_BYTES = 20 * 1024 * 1024  # 20 MB


@router.post("", response_model=PDFResponse)
async def process_pdf(
    file: UploadFile = File(...),
    session_id: str = Form(default=None),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF files are accepted.")

    data = await file.read()
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF exceeds the 20 MB size limit.")

    sid = session_id or str(uuid.uuid4())

    try:
        title, full_text = await extract_pdf_text(data, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {exc}")

    chunks = chunk_text(full_text)
    if not chunks:
        raise HTTPException(status_code=422, detail="Could not extract text chunks from PDF.")

    embeddings = await embed_texts(chunks)
    upsert_chunks(sid, chunks, embeddings)

    set_session(sid, {
        "title": title,
        "source_type": "pdf",
        "filename": file.filename,
        "chunks": chunks,
        "full_text": full_text,
    })

    return PDFResponse(
        session_id=sid,
        title=title,
        chunks=len(chunks),
        message="PDF processed successfully. You can now generate flashcards, quiz, or chat.",
    )
