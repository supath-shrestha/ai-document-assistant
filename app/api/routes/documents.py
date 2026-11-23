import logging
import httpx

from pathlib import Path
from typing import Annotated, Literal

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_ollama, get_qdrant
from app.db.session import get_db
from app.schemas.document import DocumentUploadResponse
from app.services.document_ingestion import ingest_document

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_db)],
    qdrant: Annotated[AsyncQdrantClient, Depends(get_qdrant)],
    ollama_client: Annotated[
        httpx.AsyncClient,
        Depends(get_ollama),
    ],
    chunking_strategy: Annotated[
        Literal["fixed", "recursive"],
        Form(),
    ] = "recursive",
) -> DocumentUploadResponse:
    """Upload, process and index a PDF or TXT document."""

    try:
        filename = Path(file.filename or "").name.strip()

        if not filename or filename in {".", ".."}:
            raise HTTPException(
                status_code=400,
                detail="A valid filename is required.",
            )

        extension = Path(filename).suffix.lower()

        if extension not in {".pdf", ".txt"}:
            raise HTTPException(
                status_code=415,
                detail="Only PDF and TXT files are supported.",
            )

        # Read at most one byte above the configured size limit.
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        file_content = await file.read(max_bytes + 1)

        if len(file_content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File exceeds the maximum size of "
                    f"{settings.MAX_UPLOAD_SIZE_MB} MB."
                ),
            )

        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        # Determine MIME type from the accepted extension.
        content_type = "application/pdf" if extension == ".pdf" else "text/plain"

        document = await ingest_document(
            db=db,
            qdrant=qdrant,
            ollama_client=ollama_client,
            filename=filename,
            content_type=content_type,
            file_content=file_content,
            chunking_strategy=chunking_strategy,
        )

        return DocumentUploadResponse.model_validate(document)

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Document ingestion failed.")

        raise HTTPException(
            status_code=500,
            detail="Document ingestion failed. Check server logs.",
        ) from exc

    finally:
        await file.close()
