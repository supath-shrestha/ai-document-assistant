import json
from datetime import date, datetime, time
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from pydantic import EmailStr, TypeAdapter, ValidationError
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.booking_repository import create_booking
from app.schemas.booking import BookingDetails, BookingRequest, BookingResponse
from app.services.ai.llm import generate_chat_response

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

BOOKING_TTL_SECONDS = 86400  # 24 hours
BOOKING_TIMEZONE = "Asia/Kathmandu"

EMAIL_ADAPTER = TypeAdapter(EmailStr)


QUESTIONS = {
    "name": "Could you please provide your full name?",
    "email": "What is your email address?",
    "date": (
        "What date would you prefer for your interview? "
        "Please use YYYY-MM-DD format."
    ),
    "time": (
        "What time would you prefer? "
        "Please use 24-hour HH:MM format, for example 14:30."
    ),
    "confirmation": "Would you like me to confirm this interview booking?",
}


# ---------------------------------------------------------------------
# Redis helpers
# ---------------------------------------------------------------------


def _booking_key(conversation_id: UUID) -> str:
    """Generate the Redis key for a booking conversation."""
    return f"booking:{conversation_id}"


async def _save_state(
    redis: Redis,
    conversation_id: UUID,
    state: dict,
) -> None:
    """Save booking conversation state in Redis."""
    await redis.setex(
        _booking_key(conversation_id),
        BOOKING_TTL_SECONDS,
        json.dumps(state),
    )


# ---------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------


def _parse_date(value: str) -> date:
    """Parse and validate a future interview date."""

    try:
        parsed = date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.") from exc

    today = datetime.now(ZoneInfo("Asia/Kathmandu")).date()

    if parsed <= today:
        raise ValueError(
            "The interview date must be a future date. " "Please choose another date."
        )

    return parsed


def _parse_time(value: str) -> time:
    """Parse an interview time in HH:MM format."""

    try:
        parsed = time.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(
            "Invalid time format. Please use HH:MM, " "for example 14:30."
        ) from exc

    if parsed.tzinfo is not None:
        raise ValueError("Please provide the time without a timezone.")

    if parsed.second != 0 or parsed.microsecond != 0:
        raise ValueError("Please provide time in HH:MM format, " "for example 14:30.")

    return parsed


def _validate_name(value: str) -> str:
    """Validate and normalize the candidate's name."""

    name = " ".join(value.strip().split())

    if len(name) < 2:
        raise ValueError(
            "Your name must contain at least 2 characters. "
            "Please enter your full name."
        )

    if len(name) > 255:
        raise ValueError("Your name is too long. Please enter a shorter name.")

    return name


def _validate_email(value: str) -> str:
    """Validate and normalize the candidate's email."""

    try:
        email = EMAIL_ADAPTER.validate_python(value.strip())
    except ValidationError as exc:
        raise ValueError(
            "That email address doesn't appear to be valid. "
            "Please enter a valid email address."
        ) from exc

    return str(email)


# ---------------------------------------------------------------------
# AI response helper
# ---------------------------------------------------------------------


async def _generate_reply(
    ollama_client: httpx.AsyncClient,
    instruction: str,
) -> str:
    """
    Generate a natural conversational response using Ollama.

    The booking workflow itself is controlled by Python.
    The LLM only helps phrase the response.
    """

    messages = [
        {
            "role": "system",
            "content": (
                "You are a professional interview scheduling assistant. "
                "You help candidates schedule interviews. "
                "Follow the supplied instruction exactly. "
                "Do not invent booking details, ask unrelated questions, "
                "or claim that a booking is confirmed unless instructed."
            ),
        },
        {
            "role": "user",
            "content": instruction,
        },
    ]

    try:
        response = await generate_chat_response(
            client=ollama_client,
            messages=messages,
            temperature=0.2,
        )

        return response or instruction

    except (httpx.HTTPError, ValueError, KeyError):
        # Use the deterministic instruction if Ollama is unavailable
        # or returns an unexpected response.
        return instruction


# ---------------------------------------------------------------------
# Main booking conversation service
# ---------------------------------------------------------------------


async def process_booking_message(
    request: BookingRequest,
    db: AsyncSession,
    redis: Redis,
    ollama_client: httpx.AsyncClient,
) -> BookingResponse:
    """
    Process one message in the interview booking conversation.

    Conversation flow:
        name -> email -> date -> time -> confirmation -> completed
    """

    # Create a conversation ID if this is a new booking conversation.
    conversation_id = request.conversation_id or uuid4()

    redis_key = _booking_key(conversation_id)

    # Retrieve existing booking state.
    raw_state = await redis.get(redis_key)

    # -------------------------------------------------------------
    # Start a new booking conversation
    # -------------------------------------------------------------

    if raw_state is None:
        state = {
            "step": "name",
            "candidate_name": "",
            "email": "",
            "interview_date": "",
            "interview_time": "",
            "timezone": BOOKING_TIMEZONE,
        }

        await _save_state(
            redis=redis,
            conversation_id=conversation_id,
            state=state,
        )

        # IMPORTANT:
        # Do not send the initial message to Ollama.
        # Directly ask for the candidate's name.
        return BookingResponse(
            conversation_id=conversation_id,
            reply=(
                "I'd be happy to help schedule your interview. "
                "Could you please provide your full name?"
            ),
            current_step="name",
            booking_id=None,
        )

    # -------------------------------------------------------------
    # Load existing conversation state
    # -------------------------------------------------------------

    try:
        state = json.loads(raw_state)
    except (json.JSONDecodeError, TypeError):
        await redis.delete(redis_key)

        return BookingResponse(
            conversation_id=conversation_id,
            reply=(
                "Your booking session could not be restored. "
                "Let's start again. Could you please provide your full name?"
            ),
            current_step="name",
            booking_id=None,
        )

    step = state.get("step")
    message = request.message.strip()

    # -------------------------------------------------------------
    # Step 1: Candidate name
    # -------------------------------------------------------------

    try:

        if step == "name":

            state["candidate_name"] = _validate_name(message)
            state["step"] = "email"

        # ---------------------------------------------------------
        # Step 2: Candidate email
        # ---------------------------------------------------------

        elif step == "email":

            state["email"] = _validate_email(message)
            state["step"] = "date"

        # ---------------------------------------------------------
        # Step 3: Interview date
        # ---------------------------------------------------------

        elif step == "date":

            parsed_date = _parse_date(message)

            state["interview_date"] = parsed_date.isoformat()
            state["step"] = "time"

        # ---------------------------------------------------------
        # Step 4: Interview time
        # ---------------------------------------------------------

        elif step == "time":

            parsed_time = _parse_time(message)

            state["interview_time"] = parsed_time.isoformat(timespec="minutes")

            state["step"] = "confirmation"

        # ---------------------------------------------------------
        # Step 5: Booking confirmation
        # ---------------------------------------------------------

        elif step == "confirmation":

            answer = message.lower().strip()

            if answer in {"yes", "y", "confirm", "confirmed"}:

                # Validate the timezone.
                try:
                    ZoneInfo(state["timezone"])
                except ZoneInfoNotFoundError as exc:
                    raise ValueError(
                        "The configured booking timezone is invalid."
                    ) from exc

                booking_details = BookingDetails(
                    candidate_name=state["candidate_name"],
                    email=state["email"],
                    interview_date=date.fromisoformat(state["interview_date"]),
                    interview_time=time.fromisoformat(state["interview_time"]),
                    timezone=state["timezone"],
                )

                # Persist the booking in PostgreSQL.
                booking = await create_booking(
                    db=db,
                    details=booking_details,
                )

                # Delete temporary Redis state after successful booking.
                await redis.delete(redis_key)

                return BookingResponse(
                    conversation_id=conversation_id,
                    reply=(
                        "Your interview has been successfully booked! "
                        f"Your booking reference is {booking.id}. "
                        "Thank you!"
                    ),
                    current_step="completed",
                    booking_id=booking.id,
                )

            elif answer in {"no", "n", "cancel", "cancelled"}:

                await redis.delete(redis_key)

                return BookingResponse(
                    conversation_id=conversation_id,
                    reply=(
                        "Your interview booking has been cancelled. "
                        "Feel free to start a new booking whenever "
                        "you're ready."
                    ),
                    current_step="cancelled",
                    booking_id=None,
                )

            else:

                return BookingResponse(
                    conversation_id=conversation_id,
                    reply=(
                        "Please respond with 'yes' to confirm "
                        "the booking or 'no' to cancel it."
                    ),
                    current_step="confirmation",
                    booking_id=None,
                )

        else:
            await redis.delete(redis_key)

            return BookingResponse(
                conversation_id=conversation_id,
                reply=(
                    "Your booking session is invalid or expired. "
                    "Let's start again. Could you please provide "
                    "your full name?"
                ),
                current_step="name",
                booking_id=None,
            )

    # -------------------------------------------------------------
    # Handle invalid input
    # -------------------------------------------------------------

    except ValueError as exc:

        return BookingResponse(
            conversation_id=conversation_id,
            reply=str(exc),
            current_step=step,
            booking_id=None,
        )

    except ValidationError:

        return BookingResponse(
            conversation_id=conversation_id,
            reply=(
                "Some of the booking information is invalid. "
                "Please provide the requested information again."
            ),
            current_step=step,
            booking_id=None,
        )

    # -------------------------------------------------------------
    # Save updated state
    # -------------------------------------------------------------

    await _save_state(
        redis=redis,
        conversation_id=conversation_id,
        state=state,
    )

    next_step = state["step"]

    # -------------------------------------------------------------
    # Generate the next conversational response
    # -------------------------------------------------------------

    if next_step == "confirmation":

        reply = (
            "Thank you! Here are your interview details:\n\n"
            f"Name: {state['candidate_name']}\n"
            f"Email: {state['email']}\n"
            f"Date: {state['interview_date']}\n"
            f"Time: {state['interview_time']}\n"
            f"Timezone: {state['timezone']}\n\n"
            "Would you like to confirm this booking? "
            "Please reply with 'yes' or 'no'."
        )

    else:
        reply = QUESTIONS[next_step]

    return BookingResponse(
        conversation_id=conversation_id,
        reply=reply,
        current_step=next_step,
        booking_id=None,
    )
