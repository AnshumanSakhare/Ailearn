"""
Gemini embedding helper with character-based chunking.
Uses direct httpx REST calls to avoid SDK version issues.
"""

import asyncio
from typing import List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

# Google Generative Language REST endpoint (v1beta, proven to work with embedding-001)
_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"

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


async def _embed_single(client: httpx.AsyncClient, text: str, task_type: str) -> List[float]:
    """Embed a single text string via REST."""
    model = settings.EMBEDDING_MODEL  # e.g. "embedding-001"
    url = _BASE_URL.format(model=model)
    payload = {
        "model": f"models/{model}",
        "content": {"parts": [{"text": text}]},
        "taskType": task_type,
    }
    resp = await client.post(url, params={"key": settings.GEMINI_API_KEY}, json=payload)
    resp.raise_for_status()
    return resp.json()["embedding"]["values"]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Return Gemini embeddings for a list of texts."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [_embed_single(client, t, "RETRIEVAL_DOCUMENT") for t in texts]
        return list(await asyncio.gather(*tasks))


async def embed_query(text: str) -> List[float]:
    """Embed a single query string."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        return await _embed_single(client, text, "RETRIEVAL_QUERY")

