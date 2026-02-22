"""
AI generation helpers: flashcards, quiz, and RAG-based chat.
Uses google-genai (the current Gemini SDK).
"""

import json
import re
from typing import List, AsyncIterator

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from models.schemas import Flashcard, QuizQuestion, QuizOption, ChatMessage

_client = genai.Client(api_key=settings.GEMINI_API_KEY)

_JSON_CFG = types.GenerateContentConfig(
    response_mime_type="application/json",
    temperature=0.4,
)
_CHAT_CFG = types.GenerateContentConfig(temperature=0.3)


# ---------------------------------------------------------------------------

def _extract_json(text: str):
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


# ---------------------------------------------------------------------------
# Flashcard generation
# ---------------------------------------------------------------------------

_FLASHCARD_PROMPT = """\
You are an expert educator. Given the source text below, generate {n} high-quality flashcards.
Return ONLY a valid JSON array (no markdown, no extra text) with this schema:
[
  {{"id": 1, "front": "question or term", "back": "answer or definition", "topic": "optional topic label"}},
  ...
]
Source text:
{context}
"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
async def generate_flashcards(context: str, n: int = 12) -> List[Flashcard]:
    prompt = _FLASHCARD_PROMPT.format(n=n, context=context[:12000])
    response = await _client.aio.models.generate_content(
        model=settings.CHAT_MODEL,
        contents=prompt,
        config=_JSON_CFG,
    )
    parsed = _extract_json(response.text)
    if isinstance(parsed, dict):
        parsed = parsed.get("flashcards") or next(iter(parsed.values()), [])
    return [Flashcard(**item) for item in parsed]


# ---------------------------------------------------------------------------
# Quiz generation
# ---------------------------------------------------------------------------

_QUIZ_PROMPT = """\
You are an expert educator. Given the source text below, create {n} multiple-choice quiz questions.
Return ONLY a valid JSON array (no markdown, no extra text) with this schema:
[
  {{
    "id": 1,
    "question": "...",
    "options": [
      {{"key": "A", "text": "..."}},
      {{"key": "B", "text": "..."}},
      {{"key": "C", "text": "..."}},
      {{"key": "D", "text": "..."}}
    ],
    "correct_key": "A",
    "explanation": "Brief explanation."
  }}
]
Source text:
{context}
"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
async def generate_quiz(context: str, n: int = 7) -> List[QuizQuestion]:
    prompt = _QUIZ_PROMPT.format(n=n, context=context[:12000])
    response = await _client.aio.models.generate_content(
        model=settings.CHAT_MODEL,
        contents=prompt,
        config=_JSON_CFG,
    )
    parsed = _extract_json(response.text)
    if isinstance(parsed, dict):
        parsed = parsed.get("questions") or next(iter(parsed.values()), [])
    questions = []
    for item in parsed:
        item["options"] = [QuizOption(**o) for o in item["options"]]
        questions.append(QuizQuestion(**item))
    return questions


# ---------------------------------------------------------------------------
# RAG Chat (true async streaming)
# ---------------------------------------------------------------------------

_SYSTEM = """\
You are a knowledgeable and helpful learning assistant.
Answer the user's question using ONLY the provided context from their uploaded material.
If the answer isn't in the context, say so clearly. Be concise, accurate, and educational.

Context:
{context}
"""


async def rag_chat_stream(
    context_chunks: List[str],
    history: List[ChatMessage],
    user_message: str,
) -> AsyncIterator[str]:
    """Yield Gemini response tokens via true async streaming."""
    context = "\n\n---\n\n".join(context_chunks)
    system_prompt = _SYSTEM.format(context=context)

    # Build contents list: history + current user message
    # Gemini roles: "user" | "model"
    contents = []
    for msg in history[-10:]:
        role = "model" if msg.role == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    async for chunk in await _client.aio.models.generate_content_stream(
        model=settings.CHAT_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
        ),
    ):
        if chunk.text:
            yield chunk.text
