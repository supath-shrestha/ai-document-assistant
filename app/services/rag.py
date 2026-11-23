from uuid import UUID, uuid4

import httpx
from qdrant_client import AsyncQdrantClient
from redis.asyncio import Redis

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai.llm import generate_chat_response
from app.services.conversation import (
    get_conversation_history,
    save_conversation_history,
)
from app.services.retrieval import retrieve_relevant_chunks

SYSTEM_PROMPT = """
You are a helpful document assistant.

Answer the user's questions using the supplied document context
and conversation history.

Rules:
1. Use the retrieved document context as your primary source.
2. Do not invent facts that are not supported by the context.
3. If the context does not contain the answer, clearly say so.
4. Use conversation history to understand follow-up questions.
5. Give clear, concise, and relevant answers.
6. Do not claim that information exists in a document unless
   it is supported by the retrieved context.
"""


async def process_rag_query(
    *,
    request: ChatRequest,
    redis_client: Redis,
    qdrant_client: AsyncQdrantClient,
    ollama_client: httpx.AsyncClient,
) -> ChatResponse:
    """Process a conversational RAG request."""

    conversation_id = request.conversation_id or uuid4()

    # 1. Retrieve previous conversation history.
    history = await get_conversation_history(
        redis=redis_client,
        conversation_id=conversation_id,
    )

    # 2. Retrieve relevant document chunks.
    sources = await retrieve_relevant_chunks(
        ollama_client=ollama_client,
        qdrant_client=qdrant_client,
        query=request.message,
        top_k=request.top_k,
        document_id=request.document_id,
    )

    # 3. Construct document context.
    context = "\n\n".join(
        (
            f"Document: {source.filename}\n"
            f"Chunk: {source.chunk_index}\n"
            f"Content:\n{source.text}"
        )
        for source in sources
    )

    if not context:
        context = "No relevant document content was retrieved."

    # 4. Construct the current user message with retrieved context.
    user_prompt = f"""
Retrieved document context:

{context}

Current question:

{request.message}
"""

    # 5. Construct the complete LLM message list.
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        *history,
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    # 6. Generate the answer using Ollama.
    answer = await generate_chat_response(
        client=ollama_client,
        messages=messages,
    )

    # 7. Save the original user message and assistant response.
    updated_history = [
        *history,
        {
            "role": "user",
            "content": request.message,
        },
        {
            "role": "assistant",
            "content": answer,
        },
    ]

    await save_conversation_history(
        redis=redis_client,
        conversation_id=conversation_id,
        history=updated_history,
    )

    # 8. Return the response and retrieved sources.
    return ChatResponse(
        conversation_id=conversation_id,
        answer=answer,
        sources=sources,
    )
