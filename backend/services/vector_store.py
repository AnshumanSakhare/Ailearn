"""
Vector-store helpers backed by Supabase pgvector.
Uses psycopg2 + pgvector directly — no vecs dependency.
Each session gets its own table: chunks_<session_id_safe>.
"""

import re
from typing import List

import psycopg2
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector

from config import settings


def _conn():
    conn = psycopg2.connect(settings.SUPABASE_DB_URL)
    register_vector(conn)
    return conn


def _table(session_id: str) -> str:
    """Safe table name derived from session_id."""
    safe = re.sub(r"[^a-zA-Z0-9]", "_", session_id)[:40]
    return f"chunks_{safe}"


def upsert_chunks(session_id: str, chunks: List[str], embeddings: List[List[float]]):
    """Create table if needed, then insert (chunk_text, embedding) rows."""
    table = _table(session_id)
    dim = len(embeddings[0])

    conn = _conn()
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
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS {table}_emb_idx
                ON {table} USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 10);
            """)
        conn.commit()
    finally:
        conn.close()


def query_chunks(session_id: str, query_embedding: List[float], top_k: int = None) -> List[str]:
    """Return the top-k most-similar chunk texts for a query embedding."""
    k = top_k or settings.TOP_K
    table = _table(session_id)

    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT content
                FROM {table}
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
                """,
                (query_embedding, k),
            )
            rows = cur.fetchall()
        return [row[0] for row in rows]
    except Exception:
        return []
    finally:
        conn.close()


def delete_session(session_id: str):
    table = _table(session_id)
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {table};")
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()
