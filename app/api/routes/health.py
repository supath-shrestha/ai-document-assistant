from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.session import AsyncSessionLocal

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(request: Request):
    """Check connectivity to all application dependencies."""

    services = {}

    # Check PostgreSQL.
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))

        services["postgresql"] = "healthy"

    except Exception:
        services["postgresql"] = "unavailable"

    # Check Redis.
    try:
        redis = request.app.state.redis
        await redis.ping()

        services["redis"] = "healthy"

    except Exception:
        services["redis"] = "unavailable"

    # Check Qdrant.
    try:
        qdrant = request.app.state.qdrant
        await qdrant.get_collections()

        services["qdrant"] = "healthy"

    except Exception:
        services["qdrant"] = "unavailable"

    # Determine overall application status.
    all_healthy = all(status == "healthy" for status in services.values())

    response = {
        "status": "healthy" if all_healthy else "unhealthy",
        "services": services,
    }

    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content=response,
    )
