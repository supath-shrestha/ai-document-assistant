from typing import Sequence

import httpx

from app.core.config import settings


async def generate_embeddings(
    client: httpx.AsyncClient,
    texts: Sequence[str],
) -> list[list[float]]:
    """
    Generate embeddings for a sequence of texts using Ollama.

    Args:
        client: Shared HTTPX client connected to Ollama.
        texts: Texts to convert into embedding vectors.

    Returns:
        A list of embedding vectors.

    Raises:
        ValueError: If the input contains empty texts.
        RuntimeError: If Ollama returns unexpected embeddings.
        httpx.HTTPStatusError: If the Ollama API returns an error.
    """

    if not texts:
        return []

    if any(not text.strip() for text in texts):
        raise ValueError("Input texts must not be empty.")

    response = await client.post(
        "/api/embed",
        json={
            "model": settings.OLLAMA_EMBEDDING_MODEL,
            "input": list(texts),
        },
    )

    response.raise_for_status()

    data = response.json()

    embeddings: list[list[float]] = data.get("embeddings", [])

    if len(embeddings) != len(texts):
        raise RuntimeError("Ollama returned an unexpected number of embeddings.")

    for index, embedding in enumerate(embeddings):
        if len(embedding) != settings.EMBEDDING_DIMENSIONS:
            raise RuntimeError(
                f"Embedding {index} has dimension {len(embedding)}; "
                f"expected {settings.EMBEDDING_DIMENSIONS}."
            )

    return embeddings
