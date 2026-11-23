from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from fastapi import FastAPI
from qdrant_client import AsyncQdrantClient
from redis.asyncio import Redis

from app.core.config import settings
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage external service clients during application lifespan."""

    # Initialize Redis client.
    redis_client = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )

    # Initialize Qdrant client.
    qdrant_client = AsyncQdrantClient(
        url=settings.QDRANT_URL,
    )

    # Initialize Ollama HTTP client.
    ollama_client = httpx.AsyncClient(
        base_url=settings.OLLAMA_BASE_URL,
        timeout=httpx.Timeout(180.0),
    )

    # Make clients accessible throughout the application.
    app.state.redis = redis_client
    app.state.qdrant = qdrant_client
    app.state.ollama = ollama_client

    try:
        yield
    finally:
        # Close external service clients.
        try:
            await redis_client.aclose()
        finally:
            try:
                await qdrant_client.close()
            finally:
                try:
                    await ollama_client.aclose()
                finally:
                    # Release SQLAlchemy database connections.
                    await engine.dispose()
