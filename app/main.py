from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered document ingestion, conversational RAG and interview booking API."
    ),
    version="1.0.0",
)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """
    Basic application health endpoint.
    """

    return {
        "status": "healthy",
        "application": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {
        "message": "Welcome to AI Document Assistant API",
        "docs": "/docs",
    }
