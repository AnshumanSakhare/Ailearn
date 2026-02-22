"""
Gemini embedding helper with character-based chunking.
Uses google-genai (the current Gemini SDK).
"""

from typing import List

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

_client = genai.Client(api_key=settings.GEMINI_API_KEY)

# ~4 chars per token is a reasonable approximation
_CHARS_PER_TOKEN = 4


def chunk_text(text: str, size: int = None, overlap: int = None) -> List[str]:
    """Split text into overlapping character-based chunks."""
    chunk_chars = (size or settings.CHUNK_SIZE) * _CHARS_PER_TOKEN
    overlap_chars = (overlap or settings.CHUNK_OVERLAP) * _CHARS_PER_TOKEN

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_chars, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += chunk_chars - overlap_chars
    return chunks


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Return Gemini embeddings for a list of texts (async)."""
    BATCH = 100
    all_embeddings: List[List[float]] = []

    for i in range(0, len(texts), BATCH):
        batch = texts[i : i + BATCH]
        response = await _client.aio.models.embed_content(
            model=settings.EMBEDDING_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
            ),
        )
        all_embeddings.extend([e.values for e in response.embeddings])

    return all_embeddings


async def embed_query(text: str) -> List[float]:
    """Embed a single query string."""
    response = await _client.aio.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=[text],
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
        ),
    )
    return response.embeddings[0].values
