from datetime import date, datetime, time
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, String, Time, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Booking(Base):
    """Stores confirmed interview bookings."""

    __tablename__ = "bookings"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    candidate_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    interview_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    interview_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="Asia/Kathmandu",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="confirmed",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
