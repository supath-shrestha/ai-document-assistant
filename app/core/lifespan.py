from contextlib import asynccontextmanager
from typing import AsyncIterator

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

    # Make clients accessible throughout the application.
    app.state.redis = redis_client
    app.state.qdrant = qdrant_client

    try:
        yield
    finally:
        # Close external service clients.
        await redis_client.aclose()
        await qdrant_client.close()

        # Release SQLAlchemy database connections.
        await engine.dispose()
