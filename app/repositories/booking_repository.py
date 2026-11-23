from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.schemas.booking import BookingDetails


async def create_booking(
    db: AsyncSession,
    details: BookingDetails,
) -> Booking:
    """Persist a confirmed interview booking."""

    booking = Booking(
        candidate_name=details.candidate_name,
        email=str(details.email),
        interview_date=details.interview_date,
        interview_time=details.interview_time,
        timezone=details.timezone,
        status="confirmed",
    )

    db.add(booking)

    await db.commit()
    await db.refresh(booking)

    return booking
