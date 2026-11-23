from uuid import UUID

import httpx
from qdrant_client import AsyncQdrantClient, models

from app.core.config import settings
from app.schemas.chat import ChatSource
from app.services.ai.embeddings import generate_embeddings


async def retrieve_relevant_chunks(
    *,
    ollama_client: httpx.AsyncClient,
    qdrant_client: AsyncQdrantClient,
    query: str,
    top_k: int = 5,
    document_id: UUID | None = None,
) -> list[ChatSource]:
    """Retrieve relevant document chunks from Qdrant."""

    query_embeddings = await generate_embeddings(
        client=ollama_client,
        texts=[query],
    )

    query_vector = query_embeddings[0]

    query_filter = None

    if document_id is not None:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(
                        value=str(document_id),
                    ),
                )
            ]
        )

    search_result = await qdrant_client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True,
    )

    sources: list[ChatSource] = []

    for point in search_result.points:
        payload = point.payload or {}

        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            continue

        sources.append(
            ChatSource(
                document_id=str(payload.get("document_id", "")),
                filename=str(payload.get("filename", "Unknown")),
                chunk_index=int(payload.get("chunk_index", 0)),
                score=float(point.score or 0.0),
                text=text,
            )
        )

    return sources
