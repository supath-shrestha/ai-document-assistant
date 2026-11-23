from fastapi import FastAPI

from app.core.config import settings
from app.core.lifespan import lifespan

from app.api.routes.health import router as health_router
from app.api.routes.documents import router as documents_router

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered document ingestion, "
        "conversational RAG and interview booking API."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Health endpoint: /health
app.include_router(health_router)

# Document endpoints: /api/v1/documents/...
app.include_router(
    documents_router,
    prefix=settings.API_V1_PREFIX,
)


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {
        "message": "Welcome to AI Document Assistant API",
        "docs": "/docs",
    }
