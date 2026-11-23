import logging
import uuid

import httpx
from qdrant_client import AsyncQdrantClient, models
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document
from app.services.ai.embeddings import generate_embeddings
from app.services.chunking import (
    ChunkingStrategy,
    chunk_segments,
)
from app.services.document_parser import extract_text_segments
from app.services.vector_store import ensure_document_collection

logger = logging.getLogger(__name__)


async def ingest_document(
    db: AsyncSession,
    qdrant: AsyncQdrantClient,
    ollama_client: httpx.AsyncClient,
    filename: str,
    content_type: str,
    file_content: bytes,
    chunking_strategy: ChunkingStrategy,
) -> Document:
    """Process a document and store its chunks in Qdrant."""

    # 1. Create the document record in PostgreSQL.
    document = Document(
        filename=filename,
        content_type=content_type,
        file_size=len(file_content),
        status="processing",
        chunking_strategy=chunking_strategy,
        chunk_count=0,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    document_id = document.id
    inserted_point_ids: list[str] = []

    try:
        # 2. Extract text.
        segments = extract_text_segments(
            filename=filename,
            content=file_content,
        )

        # 3. Generate chunks.
        chunks = chunk_segments(
            segments=segments,
            strategy=chunking_strategy,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        if not chunks:
            raise ValueError("No text chunks could be generated.")

        # 4. Ensure the Qdrant collection exists.
        await ensure_document_collection(qdrant)

        # 5. Generate embeddings and store vectors in batches.
        batch_size = settings.EMBEDDING_BATCH_SIZE

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]

            # Extract text from the document chunks.
            batch_texts = [chunk.text for chunk in batch]

            # Generate embeddings using Ollama.
            embeddings = await generate_embeddings(
                client=ollama_client,
                texts=batch_texts,
            )

            if len(embeddings) != len(batch):
                raise RuntimeError(
                    "Embedding response count did not match "
                    "the number of input chunks."
                )

            points: list[models.PointStruct] = []

            for chunk, embedding in zip(
                batch,
                embeddings,
                strict=True,
            ):
                # Deterministic point ID for this document chunk.
                point_id = str(
                    uuid.uuid5(
                        document_id,
                        f"chunk-{chunk.index}",
                    )
                )

                payload = {
                    "document_id": str(document_id),
                    "filename": filename,
                    "chunk_index": chunk.index,
                    "chunking_strategy": chunking_strategy,
                    "content_type": content_type,
                    "text": chunk.text,
                }

                if chunk.page_number is not None:
                    payload["page_number"] = chunk.page_number

                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload,
                    )
                )

                # Remember IDs in case cleanup is needed.
                inserted_point_ids.append(point_id)

            await qdrant.upsert(
                collection_name=settings.QDRANT_COLLECTION,
                points=points,
            )

        # 6. Mark the document as completed.
        saved_document = await db.get(Document, document_id)

        if saved_document is None:
            raise RuntimeError("Document record disappeared during ingestion.")

        saved_document.status = "completed"
        saved_document.chunk_count = len(chunks)

        await db.commit()
        await db.refresh(saved_document)

        return saved_document

    except Exception:
        # Roll back any uncommitted database changes.
        await db.rollback()

        # Remove any vectors already inserted for this document.
        if inserted_point_ids:
            try:
                await qdrant.delete(
                    collection_name=settings.QDRANT_COLLECTION,
                    points_selector=models.PointIdsList(
                        points=inserted_point_ids,
                    ),
                )

            except Exception:
                logger.exception(
                    "Could not clean up Qdrant points " "for document %s",
                    document_id,
                )

        # Mark the document record as failed.
        try:
            failed_document = await db.get(
                Document,
                document_id,
            )

            if failed_document is not None:
                failed_document.status = "failed"
                await db.commit()

        except Exception:
            await db.rollback()

            logger.exception(
                "Could not update failed status for document %s",
                document_id,
            )

        raise
