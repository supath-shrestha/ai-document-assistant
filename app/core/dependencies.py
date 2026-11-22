from fastapi import Request
from qdrant_client import AsyncQdrantClient
from redis.asyncio import Redis


def get_redis(request: Request) -> Redis:
    """Return the application's Redis client."""

    return request.app.state.redis


def get_qdrant(request: Request) -> AsyncQdrantClient:
    """Return the application's Qdrant client."""

    return request.app.state.qdrant
