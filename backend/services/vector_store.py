"""
Vector-store helpers with in-memory primary storage and optional Supabase persistence.
In-memory store always works; Supabase is used when the connection is available.
"""

import logging
import math
import re
from typing import Dict, List, Tuple

from config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory store: { session_id: [(chunk_text, embedding), ...] }
# ---------------------------------------------------------------------------
_store: Dict[str, List[Tuple[str, List[float]]]] = {}


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ---------------------------------------------------------------------------
# Optional Supabase connection (fails gracefully if paused/unavailable)
# ---------------------------------------------------------------------------
def _try_pg_upsert(session_id: str, chunks: List[str], embeddings: List[List[float]]):
    """Try to persist to Supabase pgvector. Silently skip on any error."""
    if not settings.SUPABASE_DB_URL:
        return
    try:
        import psycopg2
        from psycopg2.extras import execute_values
        from pgvector.psycopg2 import register_vector

        safe = re.sub(r"[^a-zA-Z0-9]", "_", session_id)[:40]
        table = f"chunks_{safe}"
        dim = len(embeddings[0])

        conn = psycopg2.connect(settings.SUPABASE_DB_URL, connect_timeout=5)
        register_vector(conn)
        try:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        content TEXT NOT NULL,
                        embedding vector({dim})
                    );
                """)
                cur.execute(f"TRUNCATE TABLE {table};")
                execute_values(
                    cur,
                    f"INSERT INTO {table} (content, embedding) VALUES %s",
                    [(chunk, emb) for chunk, emb in zip(chunks, embeddings)],
                )
            conn.commit()
            logger.info("Supabase pgvector upsert succeeded for session %s", session_id)
        finally:
            conn.close()
    except Exception as exc:
        logger.warning("Supabase unavailable, using in-memory only: %s", exc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def upsert_chunks(session_id: str, chunks: List[str], embeddings: List[List[float]]):
    """Store chunks in memory (always) and attempt Supabase persistence."""
    _store[session_id] = list(zip(chunks, embeddings))
    _try_pg_upsert(session_id, chunks, embeddings)


def query_chunks(session_id: str, query_embedding: List[float], top_k: int = None) -> List[str]:
    """Return top-k most-similar chunks using cosine similarity."""
    k = top_k or settings.TOP_K
    entries = _store.get(session_id, [])
    if not entries:
        return []
    scored = sorted(
        entries,
        key=lambda pair: _cosine_similarity(query_embedding, pair[1]),
        reverse=True,
    )
    return [text for text, _ in scored[:k]]


def delete_session(session_id: str):
    _store.pop(session_id, None)
