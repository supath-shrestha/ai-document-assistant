import httpx

from fastapi import Request
from qdrant_client import AsyncQdrantClient
from redis.asyncio import Redis


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


def get_qdrant(request: Request) -> AsyncQdrantClient:
    return request.app.state.qdrant


def get_ollama(request: Request) -> httpx.AsyncClient:
    return request.app.state.ollama
