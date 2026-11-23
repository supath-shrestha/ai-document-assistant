from typing import Any

import httpx

from app.core.config import settings


async def generate_chat_response(
    client: httpx.AsyncClient,
    messages: list[dict[str, Any]],
    temperature: float = 0.2,
) -> str:
    """
    Generate a chat response using the configured Ollama model.

    Args:
        client: Shared HTTPX client connected to Ollama.
        messages: Conversation messages containing roles and content.
        temperature: Controls response randomness.

    Returns:
        Generated assistant response.

    Raises:
        ValueError: If no messages are provided.
        RuntimeError: If Ollama returns an invalid response.
        httpx.HTTPStatusError: If the Ollama API returns an error.
    """

    if not messages:
        raise ValueError("At least one message is required.")

    response = await client.post(
        "/api/chat",
        json={
            "model": settings.OLLAMA_CHAT_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        },
    )

    response.raise_for_status()

    data = response.json()

    message = data.get("message")

    if not message or not isinstance(message.get("content"), str):
        raise RuntimeError("Ollama returned an invalid chat response.")

    return message["content"].strip()
