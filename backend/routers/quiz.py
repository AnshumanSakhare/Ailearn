"""POST /generate-quiz  +  POST /generate-quiz/evaluate"""

from fastapi import APIRouter, HTTPException

from models.schemas import (
    QuizRequest, QuizResponse,
    QuizEvalRequest, QuizEvalResponse, QuizEvalResult,
)
from services.session_store import get_session, update_session
from services.ai import generate_quiz

router = APIRouter()


@router.post("", response_model=QuizResponse)
async def create_quiz(body: QuizRequest):
    try:
        session = get_session(body.session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if "quiz" in session:
        return QuizResponse(session_id=body.session_id, questions=session["quiz"])

    full_text: str = session.get("full_text", "")
    if not full_text:
        raise HTTPException(status_code=422, detail="No text content found for this session.")

    try:
        questions = await generate_quiz(full_text, n=7)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {exc}")

    update_session(body.session_id, quiz=questions)
    return QuizResponse(session_id=body.session_id, questions=questions)


@router.post("/evaluate", response_model=QuizEvalResponse)
async def evaluate_quiz(body: QuizEvalRequest):
    try:
        session = get_session(body.session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    questions = session.get("quiz")
    if not questions:
        raise HTTPException(status_code=404, detail="No quiz found. Generate the quiz first.")

    results = []
    score = 0
    for q in questions:
        chosen = body.answers.get(str(q.id))
        is_correct = chosen == q.correct_key
        if is_correct:
            score += 1
        results.append(
            QuizEvalResult(
                question_id=q.id,
                correct=is_correct,
                correct_key=q.correct_key,
                explanation=q.explanation,
            )
        )

    return QuizEvalResponse(score=score, total=len(questions), results=results)
