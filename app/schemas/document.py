from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentUploadResponse(BaseModel):
    """Response returned after document ingestion."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    content_type: str
    file_size: int
    status: str
    chunking_strategy: str
    chunk_count: int
    created_at: datetime
