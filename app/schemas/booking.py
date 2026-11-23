from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BookingRequest(BaseModel):
    """Incoming message for the booking assistant."""

    message: str = Field(min_length=1, max_length=2000)
    conversation_id: UUID | None = None


class BookingResponse(BaseModel):
    """Response from the booking assistant."""

    conversation_id: UUID
    reply: str
    current_step: str
    booking_id: UUID | None = None


class BookingDetails(BaseModel):
    """Validated interview booking details."""

    candidate_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    interview_date: date
    interview_time: time
    timezone: str = "Asia/Kathmandu"


class BookingRead(BaseModel):
    """Persisted booking response."""

    id: UUID
    candidate_name: str
    email: EmailStr
    interview_date: date
    interview_time: time
    timezone: str
    status: str

    model_config = ConfigDict(from_attributes=True)
