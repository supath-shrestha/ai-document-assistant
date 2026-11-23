from qdrant_client import AsyncQdrantClient, models

from app.core.config import settings


async def ensure_document_collection(
    qdrant: AsyncQdrantClient,
) -> None:
    """Create the document collection or validate its vector dimension."""

    collection_name = settings.QDRANT_COLLECTION

    exists = await qdrant.collection_exists(
        collection_name=collection_name,
    )

    if not exists:
        await qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=settings.EMBEDDING_DIMENSIONS,
                distance=models.Distance.COSINE,
            ),
        )
        return

    collection_info = await qdrant.get_collection(
        collection_name=collection_name,
    )

    vector_config = collection_info.config.params.vectors

    if not isinstance(vector_config, models.VectorParams):
        raise RuntimeError(
            f"Collection '{collection_name}' does not use "
            "the expected single-vector configuration."
        )

    if vector_config.size != settings.EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            f"Collection '{collection_name}' has vector dimension "
            f"{vector_config.size}, but the configured embedding "
            f"dimension is {settings.EMBEDDING_DIMENSIONS}."
        )
