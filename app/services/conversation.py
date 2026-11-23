import json
from uuid import UUID

from redis.asyncio import Redis

CONVERSATION_TTL_SECONDS = 60 * 60 * 24  # 24 hours
MAX_HISTORY_MESSAGES = 20


def _conversation_key(conversation_id: UUID) -> str:
    return f"conversation:{conversation_id}"


async def get_conversation_history(
    redis: Redis,
    conversation_id: UUID,
) -> list[dict[str, str]]:
    """Retrieve conversation history from Redis."""

    key = _conversation_key(conversation_id)

    stored_history = await redis.get(key)

    if stored_history is None:
        return []

    history: list[dict[str, str]] = json.loads(stored_history)

    return history


async def save_conversation_history(
    redis: Redis,
    conversation_id: UUID,
    history: list[dict[str, str]],
) -> None:
    """Save conversation history to Redis."""

    key = _conversation_key(conversation_id)

    # Retain only the most recent messages.
    history = history[-MAX_HISTORY_MESSAGES:]

    await redis.setex(
        key,
        CONVERSATION_TTL_SECONDS,
        json.dumps(history),
    )


async def append_message(
    redis: Redis,
    conversation_id: UUID,
    role: str,
    content: str,
) -> None:
    """Append a message to the existing conversation."""

    history = await get_conversation_history(
        redis,
        conversation_id,
    )

    history.append(
        {
            "role": role,
            "content": content,
        }
    )

    await save_conversation_history(
        redis,
        conversation_id,
        history,
    )
