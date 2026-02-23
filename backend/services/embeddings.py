"""
Gemini embedding helper with character-based chunking.
Uses google-generativeai (stable SDK with proven embedContent support).
"""

import asyncio
from typing import List

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

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


def _embed_batch(batch: List[str]) -> List[List[float]]:
    """Synchronous batch embed using google-generativeai."""
    result = genai.embed_content(
        model=settings.EMBEDDING_MODEL,
        content=batch,
        task_type="retrieval_document",
    )
    # When content is a list, result["embedding"] is a list of embedding vectors
    embeddings = result["embedding"]
    # Normalise: single text returns a flat list, wrap it
    if embeddings and not isinstance(embeddings[0], list):
        embeddings = [embeddings]
    return embeddings


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Return Gemini embeddings for a list of texts (async via thread)."""
    BATCH = 100
    all_embeddings: List[List[float]] = []

    for i in range(0, len(texts), BATCH):
        batch = texts[i : i + BATCH]
        embeddings = await asyncio.to_thread(_embed_batch, batch)
        all_embeddings.extend(embeddings)

    return all_embeddings


async def embed_query(text: str) -> List[float]:
    """Embed a single query string."""
    def _run():
        result = genai.embed_content(
            model=settings.EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_query",
        )
        return result["embedding"]

    return await asyncio.to_thread(_run)
