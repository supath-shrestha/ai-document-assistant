from dataclasses import dataclass
from typing import Literal

from app.services.document_parser import TextSegment

ChunkingStrategy = Literal["fixed", "recursive"]


@dataclass(frozen=True)
class DocumentChunk:
    """Represents a chunk generated from a document."""

    index: int
    text: str
    page_number: int | None = None


def fixed_size_chunk(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """Split text into fixed-size overlapping chunks."""

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "Chunk overlap must be non-negative " "and smaller than chunk size."
        )

    chunks: list[str] = []

    step = chunk_size - chunk_overlap
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start += step

    return chunks


def recursive_chunk(
    text: str,
    chunk_size: int,
    separators: tuple[str, ...] = (
        "\n\n",
        "\n",
        ". ",
        " ",
        "",
    ),
) -> list[str]:
    """Split text recursively using meaningful separators."""

    text = text.strip()

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if len(text) <= chunk_size:
        return [text]

    if not separators:
        return [
            text[start : start + chunk_size]
            for start in range(0, len(text), chunk_size)
        ]

    separator = separators[0]

    if separator not in text:
        return recursive_chunk(
            text,
            chunk_size,
            separators[1:],
        )

    pieces = text.split(separator)

    chunks: list[str] = []
    current = ""

    for piece in pieces:
        if not piece:
            continue

        candidate = f"{current}{separator}{piece}" if current else piece

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current.strip())

        if len(piece) > chunk_size:
            chunks.extend(
                recursive_chunk(
                    piece,
                    chunk_size,
                    separators[1:],
                )
            )
            current = ""

        else:
            current = piece

    if current:
        chunks.append(current.strip())

    return chunks


def chunk_segments(
    segments: list[TextSegment],
    strategy: ChunkingStrategy,
    chunk_size: int,
    chunk_overlap: int,
) -> list[DocumentChunk]:
    """Apply a selected chunking strategy to extracted segments."""

    chunks: list[DocumentChunk] = []

    for segment in segments:

        if strategy == "fixed":
            text_chunks = fixed_size_chunk(
                text=segment.text,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

        elif strategy == "recursive":
            text_chunks = recursive_chunk(
                text=segment.text,
                chunk_size=chunk_size,
            )

        else:
            raise ValueError("Unsupported chunking strategy.")

        for text in text_chunks:
            chunks.append(
                DocumentChunk(
                    index=len(chunks),
                    text=text,
                    page_number=segment.page_number,
                )
            )

    return chunks
