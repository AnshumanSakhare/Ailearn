"""POST /generate-flashcards"""

from fastapi import APIRouter, HTTPException

from models.schemas import FlashcardRequest, FlashcardsResponse
from services.session_store import get_session, update_session
from services.ai import generate_flashcards

router = APIRouter()


@router.post("", response_model=FlashcardsResponse)
async def create_flashcards(body: FlashcardRequest):
    try:
        session = get_session(body.session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    # Return cached flashcards if already generated
    if "flashcards" in session:
        return FlashcardsResponse(
            session_id=body.session_id,
            flashcards=session["flashcards"],
        )

    full_text: str = session.get("full_text", "")
    if not full_text:
        raise HTTPException(status_code=422, detail="No text content found for this session.")

    try:
        cards = await generate_flashcards(full_text, n=12)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Flashcard generation failed: {exc}")

    update_session(body.session_id, flashcards=cards)

    return FlashcardsResponse(session_id=body.session_id, flashcards=cards)
