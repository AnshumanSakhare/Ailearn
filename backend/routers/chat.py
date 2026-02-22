"""POST /chat – RAG-based streaming chat endpoint."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models.schemas import ChatRequest
from services.session_store import get_session
from services.embeddings import embed_query
from services.vector_store import query_chunks
from services.ai import rag_chat_stream
from config import settings

router = APIRouter()


@router.post("")
async def chat(body: ChatRequest):
    try:
        get_session(body.session_id)   # validates session exists
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    # Embed the user's question and retrieve relevant chunks
    q_emb = await embed_query(body.message)
    context_chunks = query_chunks(body.session_id, q_emb, top_k=settings.TOP_K)

    if not context_chunks:
        # Fallback: use first N chunks from session
        session = get_session(body.session_id)
        context_chunks = session.get("chunks", [])[:settings.TOP_K]

    async def token_stream():
        async for token in rag_chat_stream(
            context_chunks=context_chunks,
            history=body.history or [],
            user_message=body.message,
        ):
            yield token

    return StreamingResponse(token_stream(), media_type="text/plain")
