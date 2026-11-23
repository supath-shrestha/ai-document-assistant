from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class TextSegment:
    """Represents extracted text and its original page."""

    text: str
    page_number: int | None = None


def extract_text_segments(
    filename: str,
    content: bytes,
) -> list[TextSegment]:
    """Extract text from PDF or TXT documents."""

    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        try:
            reader = PdfReader(BytesIO(content))

            if reader.is_encrypted:
                raise ValueError("Password-protected PDFs are not supported.")

            segments: list[TextSegment] = []

            for page_number, page in enumerate(
                reader.pages,
                start=1,
            ):
                text = (page.extract_text() or "").strip()

                if text:
                    segments.append(
                        TextSegment(
                            text=text,
                            page_number=page_number,
                        )
                    )

        except ValueError:
            raise

        except Exception as exc:
            raise ValueError(
                "Could not read this PDF. " "The file may be corrupted or unsupported."
            ) from exc

    elif extension == ".txt":
        try:
            text = content.decode("utf-8-sig").strip()

        except UnicodeDecodeError as exc:
            raise ValueError("TXT files must use UTF-8 encoding.") from exc

        segments = [TextSegment(text=text)] if text else []

    else:
        raise ValueError("Only PDF and TXT files are supported.")

    if not segments:
        raise ValueError("No extractable text was found in the document.")

    return segments
