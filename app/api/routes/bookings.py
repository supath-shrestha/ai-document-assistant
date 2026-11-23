import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_ollama, get_redis
from app.db.session import get_db
from app.schemas.booking import BookingRequest, BookingResponse
from app.services.booking import process_booking_message

router = APIRouter(
    prefix="/bookings",
    tags=["Interview Booking"],
)


@router.post(
    "/conversation",
    response_model=BookingResponse,
    status_code=status.HTTP_200_OK,
)
async def booking_conversation(
    request: BookingRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    ollama_client: httpx.AsyncClient = Depends(get_ollama),
) -> BookingResponse:
    """Collect and confirm interview booking details conversationally."""

    try:
        return await process_booking_message(
            request=request,
            db=db,
            redis=redis,
            ollama_client=ollama_client,
        )

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI service is temporarily unavailable.",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the booking.",
        ) from exc
