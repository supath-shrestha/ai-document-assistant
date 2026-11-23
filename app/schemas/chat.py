from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """Request schema for a document-based conversation."""

    message: str = Field(
        min_length=1,
        max_length=4000,
        description="The user's question.",
    )

    conversation_id: UUID | None = Field(
        default=None,
        description="Existing conversation ID, or omit to start a new conversation.",
    )

    document_id: UUID | None = Field(
        default=None,
        description="Optional document ID to restrict retrieval.",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of relevant document chunks to retrieve.",
    )


class ChatSource(BaseModel):
    """A document chunk used to generate an answer."""

    document_id: str
    filename: str
    chunk_index: int
    score: float
    text: str


class ChatResponse(BaseModel):
    """Response schema for conversational RAG."""

    conversation_id: UUID
    answer: str
    sources: list[ChatSource] = Field(default_factory=list)


class ConversationMessage(BaseModel):
    """A message stored in conversation history."""

    role: str
    content: str

    model_config = ConfigDict(extra="forbid")
