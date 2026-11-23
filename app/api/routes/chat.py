import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from qdrant_client import AsyncQdrantClient
from redis.asyncio import Redis

from app.core.dependencies import (
    get_ollama,
    get_qdrant,
    get_redis,
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag import process_rag_query

router = APIRouter(
    prefix="/chat",
    tags=["Conversational RAG"],
)


@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def chat(
    request: ChatRequest,
    redis_client: Redis = Depends(get_redis),
    qdrant_client: AsyncQdrantClient = Depends(get_qdrant),
    ollama_client: httpx.AsyncClient = Depends(get_ollama),
) -> ChatResponse:
    """Answer questions using uploaded documents and conversation history."""

    try:
        return await process_rag_query(
            request=request,
            redis_client=redis_client,
            qdrant_client=qdrant_client,
            ollama_client=ollama_client,
        )

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama service is unavailable.",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your question.",
        ) from exc
